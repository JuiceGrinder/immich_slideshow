"""Config flow for Immich Slideshow integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_API_KEY, 
    CONF_SERVER_URL, 
    CONF_ALBUM_ID, 
    CONF_UPDATE_INTERVAL, 
    CONF_USE_THUMBNAILS,
    CONF_RESPECT_CARD_SIZE,
    CONF_CROP_TO_FIT,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_USE_THUMBNAILS,
    DEFAULT_RESPECT_CARD_SIZE,
    DEFAULT_CROP_TO_FIT,
    DOMAIN
)
from .immich_client import ImmichClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SERVER_URL): str,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_ALBUM_ID): str,
        vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600)),
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    server_url = data[CONF_SERVER_URL].strip()
    
    # Validate server URL format
    if not server_url.startswith(('http://', 'https://')):
        raise ValueError("Server URL must start with http:// or https://")
    
    # Check for common placeholder values
    placeholder_hosts = ['your.immich.server', 'localhost', '127.0.0.1', 'example.com', 'immich.example.com']
    from urllib.parse import urlparse
    parsed_url = urlparse(server_url)
    
    if parsed_url.hostname in placeholder_hosts:
        _LOGGER.error("Detected placeholder hostname: %s", parsed_url.hostname)
        raise ValueError(f"Please replace '{parsed_url.hostname}' with your actual Immich server hostname")
    
    client = ImmichClient(server_url, data[CONF_API_KEY])
    
    try:
        await hass.async_add_executor_job(client.test_connection)
    except Exception as exc:
        _LOGGER.error("Unable to connect to Immich server: %s", exc)
        raise CannotConnect from exc

    return {"title": f"Immich ({server_url})"}

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Immich Slideshow."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Immich Slideshow."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=self.config_entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600)),
                vol.Optional(
                    CONF_USE_THUMBNAILS,
                    default=self.config_entry.options.get(CONF_USE_THUMBNAILS, DEFAULT_USE_THUMBNAILS),
                ): bool,
                vol.Optional(
                    CONF_RESPECT_CARD_SIZE,
                    default=self.config_entry.options.get(CONF_RESPECT_CARD_SIZE, DEFAULT_RESPECT_CARD_SIZE),
                ): bool,
                vol.Optional(
                    CONF_CROP_TO_FIT,
                    default=self.config_entry.options.get(CONF_CROP_TO_FIT, DEFAULT_CROP_TO_FIT),
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=options_schema
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""