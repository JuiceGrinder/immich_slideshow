"""Constants for the Immich Slideshow integration."""

DOMAIN = "immich_slideshow"
PLATFORMS = ["sensor", "camera"]

CONF_SERVER_URL = "server_url"
CONF_API_KEY = "api_key"
CONF_ALBUM_ID = "album_id"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_USE_THUMBNAILS = "use_thumbnails"

DEFAULT_UPDATE_INTERVAL = 30
DEFAULT_NAME = "Immich Slideshow"
DEFAULT_USE_THUMBNAILS = True

# Display labels for config flow
CONF_SERVER_URL_LABEL = "Server URL"
CONF_API_KEY_LABEL = "API Key"
CONF_ALBUM_ID_LABEL = "Album ID (optional)"
CONF_UPDATE_INTERVAL_LABEL = "Image Display Interval (seconds)"