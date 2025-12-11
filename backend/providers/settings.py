from config.app_config import AppConfig
from shared.logger import logger
from functools import lru_cache
import umami


app_config = AppConfig.get_instance()

@lru_cache(maxsize=1)
def get_umami_settings():
    try:        
        umami_url = app_config.get("umami_url", "")
        umami_website_name = app_config.get("umami_website_name", "unifai")
        umami_username = app_config.get("umami_username", "")
        umami_password = app_config.get("umami_password", "")        
        # Validate required configuration
        if not umami_url or umami_url == "0.0.0.0":
            raise ValueError("Umami URL is not configured")
        if not umami_username or umami_username == "dummy":
            raise ValueError("Umami username is not configured")
        if not umami_password or umami_password == "dummy":
            raise ValueError("Umami password is not configured")
        if not umami_website_name:
            raise ValueError("Umami website name is not configured")        
        umami.set_url_base(umami_url)
        umami.login(umami_username, umami_password)
        websites = umami.websites()
        website_info = next(w for w in websites if w.name == umami_website_name)
        website_id = website_info.id
        return {"umami_url": umami_url, "website_id": website_id}
    except StopIteration:
        logger.error(f"Umami website not found: {umami_website_name}")
        raise ValueError(f"Website '{umami_website_name}' not found in Umami")
    except Exception as e:
        logger.error(f"Failed to get Umami website ID: {umami_website_name}: {e}")
        raise
