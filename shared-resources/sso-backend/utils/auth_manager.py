"""
Authentication Manager for Keycloak SSO Integration
Handles user authentication, session management, and token validation
"""
import os
import jwt
import requests
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, redirect, url_for, current_app
from authlib.integrations.flask_client import OAuth
from authlib.common.errors import AuthlibBaseError
from shared.logger import logger
from config.app_config import AppConfig
from urllib.parse import urlparse, parse_qs
import threading

config = AppConfig.get_instance()

class AuthManager:
    def __init__(self, app=None):
        self.app = app
        self.oauth = None
        self.keycloak_client = None
        self.backend_env = config.get('backend_env', 'development')
        # In-memory cache for OAuth state -> redirect_path mapping
        # Key: OAuth state string, Value: (redirect_path, timestamp)
        self._oauth_state_cache = {}
        self._cache_lock = threading.Lock()
        # Clean up expired entries every 10 minutes (OAuth states expire after ~10 min)
        self._cache_cleanup_interval = timedelta(minutes=10)
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the auth manager with Flask app"""
        self.app = app
        
        # Set up secret key for sessions (still needed for user session after auth)
        if not app.secret_key:
            secret_key = config.get('secret_key')
            if not secret_key:
                secret_key = 'dev-secret-key-fixed-for-session-persistence-change-in-production'
                logger.warning("Using default development secret key - set 'secret_key' in config for production!")
            app.secret_key = secret_key
        
        # Configure OAuth
        self.oauth = OAuth(app)
        
        # Register Keycloak client
        keycloak_base_url = config.keycloak_base_url
        client_id = config.client_id
        client_secret = config.client_secret
        realm = config.get('keycloak_realm', 'master')
        
        if not all([keycloak_base_url, client_id, client_secret]):
            raise ValueError("Missing required Keycloak configuration")
        
        self.keycloak_client = self.oauth.register(
            name='keycloak',
            client_id=client_id,
            client_secret=client_secret,
            server_metadata_url=f"{keycloak_base_url}/realms/{realm}/.well-known/openid-configuration",
            client_kwargs={
                'scope': 'openid email profile',
            }
        )
        
        # Register auth routes
        self._register_auth_routes()
        
        # Set up session configuration (for user session after authentication)
        is_production = config.backend_env == "production"
        app.config.update({
            'SESSION_COOKIE_SECURE': is_production,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'None' if is_production else 'Lax',
            'SESSION_COOKIE_PATH': '/',
            'PERMANENT_SESSION_LIFETIME': timedelta(hours=10)
        })
    
    def _store_redirect_path(self, state: str, redirect_path: str):
        """Store redirect path for a given OAuth state"""
        with self._cache_lock:
            self._oauth_state_cache[state] = (redirect_path, datetime.now())
            logger.info(f"[STATE_CACHE] Stored redirect_path '{redirect_path}' for state '{state[:20]}...'")
    
    def _store_redirect_path_fallback(self, redirect_path: str) -> str:
        """Store redirect path with a fallback key (timestamp-based) in case state extraction fails"""
        with self._cache_lock:
            # Use timestamp as fallback key
            fallback_key = f"_fallback_{datetime.now().timestamp()}"
            self._oauth_state_cache[fallback_key] = (redirect_path, datetime.now())
            logger.info(f"[STATE_CACHE] Stored redirect_path '{redirect_path}' with fallback key")
            return fallback_key
    
    def _get_redirect_path(self, state: str, remove_after_use: bool = False) -> str:
        """Get redirect path for a given OAuth state, or try fallback, or '/' if not found
        
        Args:
            state: The OAuth state parameter
            remove_after_use: If True, remove from cache after retrieval (default: False, keep for retries)
        """
        with self._cache_lock:
            # First try exact state match
            if state in self._oauth_state_cache:
                redirect_path, timestamp = self._oauth_state_cache[state]
                # Check if entry is too old (more than 15 minutes)
                if datetime.now() - timestamp < timedelta(minutes=15):
                    logger.info(f"[STATE_CACHE] Found redirect_path '{redirect_path}' for state '{state[:20]}...'")
                    # Only remove if explicitly requested (after successful auth)
                    if remove_after_use:
                        del self._oauth_state_cache[state]
                    return redirect_path
                else:
                    # Expired entry, remove it
                    del self._oauth_state_cache[state]
                    logger.warning(f"[STATE_CACHE] Expired entry for state '{state[:20]}...'")
            
            # Fallback: try to find the most recent fallback entry (within last 2 minutes)
            # This handles cases where state extraction failed but we stored a fallback
            now = datetime.now()
            fallback_entries = [
                (key, path, ts) for key, (path, ts) in self._oauth_state_cache.items()
                if key.startswith('_fallback_') and (now - ts) < timedelta(minutes=2)
            ]
            if fallback_entries:
                # Get the most recent fallback entry
                fallback_entries.sort(key=lambda x: x[2], reverse=True)
                fallback_key, redirect_path, _ = fallback_entries[0]
                logger.info(f"[STATE_CACHE] Using fallback redirect_path '{redirect_path}' (state extraction may have failed)")
                if remove_after_use:
                    del self._oauth_state_cache[fallback_key]
                return redirect_path
            
            return '/'
    
    def _cleanup_expired_states(self):
        """Remove expired state entries from cache"""
        with self._cache_lock:
            now = datetime.now()
            expired_states = [
                state for state, (_, timestamp) in self._oauth_state_cache.items()
                if now - timestamp > timedelta(minutes=15)
            ]
            for state in expired_states:
                del self._oauth_state_cache[state]
            if expired_states:
                logger.info(f"[STATE_CACHE] Cleaned up {len(expired_states)} expired state entries")
    
    def _register_auth_routes(self):
        """Register authentication routes"""
        
        @self.app.route('/api/auth/login')
        def login():
            """Initiate OAuth login flow"""
            # Get the redirect URL from query parameter (where to send user after auth)
            redirect_path = request.args.get('redirect', '/')
            # Ensure redirect_path starts with / and is safe
            if not redirect_path.startswith('/'):
                redirect_path = '/'
            logger.info(f"[LOGIN] Redirect path requested: {redirect_path}")
            
            # Get the OAuth callback redirect URI
            redirect_uri = config.get(
                'redirect_url',
                url_for('auth_callback', _external=True, _scheme='https') 
                if config.backend_env == "production" 
                else f"http://{config.hostname_local}:{config.port}/api/auth/callback"
            )
            
            # Create the OAuth redirect - this generates a state parameter
            response = self.keycloak_client.authorize_redirect(redirect_uri)
            
            # Try multiple methods to extract the state
            state = None
            
            # Method 1: Extract from session (authlib stores it there)
            # There might be multiple states - get the most recent one (last in the list)
            session_keys = list(session.keys())
            logger.info(f"[LOGIN] Session keys after authorize_redirect: {session_keys}")
            oauth_states = [key for key in session_keys if key.startswith('_state_keycloak_')]
            if oauth_states:
                # Get the most recent state (the one just created by authorize_redirect)
                # Usually the last one in the list is the newest
                latest_state_key = oauth_states[-1]
                state = latest_state_key.replace('_state_keycloak_', '')
                logger.info(f"[LOGIN] Found {len(oauth_states)} OAuth states in session, using latest: {latest_state_key} -> state: {state[:30]}...")
                
                # Store redirect_path for ALL states to be safe (in case authlib uses a different one)
                for state_key in oauth_states:
                    state_val = state_key.replace('_state_keycloak_', '')
                    self._store_redirect_path(state_val, redirect_path)
                logger.info(f"[LOGIN] Stored redirect_path for all {len(oauth_states)} states")
            
            # Method 2: Extract from redirect URL Location header
            if not state:
                redirect_location = response.headers.get('Location', '')
                logger.info(f"[LOGIN] Redirect Location header: {redirect_location[:200]}..." if len(redirect_location) > 200 else f"[LOGIN] Redirect Location header: {redirect_location}")
                if redirect_location:
                    try:
                        parsed = urlparse(redirect_location)
                        query_params = parse_qs(parsed.query)
                        state_list = query_params.get('state', [])
                        if state_list:
                            state = state_list[0]
                            logger.info(f"[LOGIN] Found state in redirect URL: {state[:30]}...")
                    except Exception as e:
                        logger.warning(f"[LOGIN] Error parsing redirect URL: {str(e)}")
            
            if state:
                # Already stored above for all states, just log
                logger.info(f"[LOGIN] Successfully stored redirect_path '{redirect_path}' for state '{state[:30]}...' (and all other states)")
            else:
                # State extraction failed - store as fallback so we can still redirect correctly
                logger.warning(f"[LOGIN] FAILED to extract state! Session keys: {session_keys}, Location: {response.headers.get('Location', 'NONE')[:200]}")
                logger.warning(f"[LOGIN] Storing redirect_path '{redirect_path}' as fallback (will try to match in callback)")
                self._store_redirect_path_fallback(redirect_path)
            
            # Clean up expired states periodically
            self._cleanup_expired_states()
            
            return response

        @self.app.route('/api/auth/callback')
        def auth_callback():
            """Handle OAuth callback"""
            try:
                # Get the state parameter from the callback URL
                request_state = request.args.get('state', 'NOT_PROVIDED')
                logger.info(f"[CALLBACK] Received callback with state: {request_state[:30]}..." if len(request_state) > 30 else f"[CALLBACK] Received callback with state: {request_state}")
                
                # Log current cache contents for debugging
                with self._cache_lock:
                    cache_size = len(self._oauth_state_cache)
                    logger.info(f"[CALLBACK] State cache has {cache_size} entries")
                    if cache_size > 0:
                        cache_states = list(self._oauth_state_cache.keys())[:5]  # Show first 5
                        logger.info(f"[CALLBACK] Cache states (first 5): {[s[:20] + '...' for s in cache_states]}")
                
                # Get the redirect path from our cache using the state
                # Do this BEFORE processing the OAuth callback so we have it even if callback fails
                redirect_path = self._get_redirect_path(request_state)
                logger.info(f"[CALLBACK] Retrieved redirect_path: '{redirect_path}' for state '{request_state[:30]}...'")
                
                # Store redirect_path temporarily in case we need it in error handling
                # (We'll use it in the success redirect, and it's already retrieved for error case)
                
                # Process the OAuth callback
                token = self.keycloak_client.authorize_access_token()
                userinfo = self.keycloak_client.userinfo()
                
                # Calculate session expiration (10 hours from now)
                session_created_at = datetime.now()
                session_expires_at = session_created_at + timedelta(hours=10)
                
                # Store user info in session
                session.permanent = True
                session['user'] = {
                    'username': userinfo.get('preferred_username'),
                    'email': userinfo.get('email'),
                    'name': userinfo.get('name'),
                    'sub': userinfo.get('sub'),
                    'session_created_at': session_created_at.timestamp(),
                    'session_expires_at': session_expires_at.timestamp(),
                    'token_expires_at': token.get('expires_at', 0)
                }
                session['access_token'] = token.get('access_token')
                session['refresh_token'] = token.get('refresh_token')
                session['token_expires_at'] = token.get('expires_at', 0)
                
                logger.info(f"User {userinfo.get('preferred_username')} authenticated successfully")
                
                # Ensure we have a valid redirect_path (should already be set above)
                if not redirect_path or redirect_path == '/':
                    # Last resort: try to get from fallback one more time
                    redirect_path = self._get_redirect_path(request_state, remove_after_use=False)
                    if redirect_path == '/':
                        logger.warning(f"[CALLBACK] Could not find redirect_path, defaulting to '/'")
                
                # Now that auth succeeded, remove from cache (cleanup)
                self._get_redirect_path(request_state, remove_after_use=True)
                
                # Redirect to frontend with explicit URL
                final_url = f"{config.frontend_url}{redirect_path}?auth=success"
                logger.info(f"[CALLBACK] Successfully authenticated, redirecting to: {final_url}")
                return redirect(final_url)
                
            except AuthlibBaseError as e:
                error_msg = str(e)
                logger.error(f"Authentication error: {error_msg}")
                
                # Get redirect path from cache if available (even on error, preserve the redirect)
                request_state = request.args.get('state', '')
                redirect_path = self._get_redirect_path(request_state, remove_after_use=False) if request_state else '/'
                
                # If we still don't have a redirect_path, try fallback
                if redirect_path == '/' and request_state:
                    logger.info(f"[CALLBACK] Trying fallback lookup for state '{request_state[:30]}...'")
                    redirect_path = self._get_redirect_path(request_state, remove_after_use=False)  # Try again with fallback logic
                
                # If still no redirect_path, check all cache entries (maybe state mismatch but we have the path stored)
                if redirect_path == '/':
                    with self._cache_lock:
                        # Get the most recent redirect_path from cache (any state)
                        if self._oauth_state_cache:
                            # Sort by timestamp, get most recent
                            entries = [(path, ts) for key, (path, ts) in self._oauth_state_cache.items() if not key.startswith('_fallback_')]
                            if entries:
                                entries.sort(key=lambda x: x[1], reverse=True)
                                redirect_path = entries[0][0]
                                logger.info(f"[CALLBACK] Using most recent redirect_path from cache: '{redirect_path}'")
                
                # Redirect to frontend with explicit URL
                # IMPORTANT: Include the redirect parameter so the next login attempt preserves it
                redirect_url = f"{config.frontend_url}{redirect_path}?auth=error"
                if redirect_path != '/':
                    # Add redirect parameter so frontend can preserve it on retry
                    redirect_url += f"&redirect={redirect_path.replace('/', '%2F')}"
                logger.info(f"[CALLBACK] Authentication error, redirecting to: {redirect_url}")
                return redirect(redirect_url)
        
        @self.app.route('/api/auth/logout', methods=['POST'])
        def logout():
            """Logout user and clear session"""
            username = session.get('user', {}).get('username', 'Unknown')
            session.clear()
            logger.info(f"User {username} logged out")
            return jsonify({'message': 'Logged out successfully'})
        
        @self.app.route('/api/auth/user')
        def get_current_user():
            """Get current user information"""
            if not self.is_authenticated():
                return jsonify({'error': 'Not authenticated'}), 401
            
            # Check if session has expired (requires re-authentication)
            if self._is_session_expired():
                session.clear()
                return jsonify({'error': 'Session expired'}), 401
            
            # Check if access token needs refresh (but session is still valid)
            if self._should_refresh_token():
                if not self._refresh_access_token():
                    return jsonify({'error': 'Token refresh failed'}), 401
            
            return jsonify({
                'user': session.get('user'),
                'authenticated': True
            })
        
        @self.app.route('/api/auth/refresh', methods=['POST'])
        def refresh_token():
            """Refresh access token"""
            if not session.get('refresh_token'):
                return jsonify({'error': 'No refresh token available'}), 401
            
            # Check if session has expired first
            if self._is_session_expired():
                session.clear()
                return jsonify({'error': 'Session expired'}), 401
            
            if self._refresh_access_token():
                return jsonify({'message': 'Token refreshed successfully'})
            else:
                return jsonify({'error': 'Failed to refresh token'}), 401
    
    def is_authenticated(self):
        """Check if user is authenticated and session is valid"""
        has_session = 'user' in session and 'access_token' in session
        if not has_session:
            return False
        
        # Check if session has expired
        if self._is_session_expired():
            return False

        return True
    
    def get_current_user(self):
        """Get current user from session"""
        return session.get('user')
    
    def _is_session_expired(self):
        """Check if the user session has expired (requires re-authentication)"""
        session_expires_at = session.get('user', {}).get('session_expires_at', 0)
        if not session_expires_at:
            return True
        
        current_time = datetime.now().timestamp()
        is_expired = current_time >= session_expires_at
        
        if is_expired:
            logger.info(f"Session expired at {datetime.fromtimestamp(session_expires_at).strftime('%Y-%m-%d %H:%M:%S')}")
        
        return is_expired
    
    def _should_refresh_token(self):
        """Check if access token should be refreshed (expires in next 5 minutes)"""
        token_expires_at = session.get('token_expires_at', 0)
        if not token_expires_at:
            return True
        
        current_time = datetime.now().timestamp()
        
        # Refresh if token expires in the next minute
        should_refresh = current_time >= (token_expires_at - 60)  # 1 minute buffer
        return should_refresh
    
    def _refresh_access_token(self):
        """Refresh the access token using refresh token"""
        refresh_token = session.get('refresh_token')
        if not refresh_token:
            logger.error("No refresh token available")
            return False
        
        try:
            # Use the OAuth client to refresh token
            token = self.keycloak_client.fetch_access_token(
                refresh_token=refresh_token
            )
            
            # Update session with new token info
            session['access_token'] = token.get('access_token')
            if token.get('refresh_token'):
                session['refresh_token'] = token.get('refresh_token')
            
            # Update token expiration (but keep session expiration unchanged)
            session['token_expires_at'] = token.get('expires_at', 0)
            session['user']['token_expires_at'] = token.get('expires_at', 0)
            logger.info("Access token refreshed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to refresh token: {str(e)}")
            return False

def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_manager = current_app.extensions.get('auth_manager')
        if not auth_manager or not auth_manager.is_authenticated():
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if access token needs refresh (but don't fail if session is still valid)
        if auth_manager._should_refresh_token():
            if not auth_manager._refresh_access_token():
                logger.warning("Token refresh failed, but continuing with existing token")
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Helper function to get current user"""
    auth_manager = current_app.extensions.get('auth_manager')
    if auth_manager and auth_manager.is_authenticated():
        return auth_manager.get_current_user()
    return None
