"""LDAP user and group search endpoints."""
from flask import Blueprint, jsonify, request
from utils.auth_manager import require_auth
from ldap.client import MIN_QUERY_LENGTH

ldap_bp = Blueprint("ldap", __name__)

# Singleton client, set by app.py at startup
ldap_client = None


@ldap_bp.route("/users", methods=["GET"])
@require_auth
def search_users():
    """Search LDAP users by query string."""
    query = request.args.get("q", "")
    if len(query) < MIN_QUERY_LENGTH:
        return jsonify({"error": f"query must be at least {MIN_QUERY_LENGTH} characters"}), 400

    if ldap_client is None:
        return jsonify({"users": []})

    try:
        users = ldap_client.search_users(query)
        return jsonify({"users": [u.to_dict() for u in users]})
    except Exception as e:
        return jsonify({"error": "LDAP search unavailable"}), 503


@ldap_bp.route("/users/<uid>", methods=["GET"])
@require_auth
def get_user(uid):
    """Get a single LDAP user by UID."""
    if not uid:
        return jsonify({"error": "uid is required"}), 400

    if ldap_client is None:
        return jsonify({"error": "LDAP not configured"}), 404

    try:
        user = ldap_client.get_user(uid)
        if user is None:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user.to_dict())
    except Exception as e:
        return jsonify({"error": "Failed to look up user"}), 500


@ldap_bp.route("/groups", methods=["GET"])
@require_auth
def search_groups():
    """Search LDAP groups by query string."""
    query = request.args.get("q", "")
    if len(query) < MIN_QUERY_LENGTH:
        return jsonify({"error": f"query must be at least {MIN_QUERY_LENGTH} characters"}), 400

    if ldap_client is None:
        return jsonify({"groups": []})

    try:
        groups = ldap_client.search_groups(query)
        return jsonify({"groups": [g.to_dict() for g in groups]})
    except Exception as e:
        return jsonify({"error": "LDAP search unavailable"}), 503
