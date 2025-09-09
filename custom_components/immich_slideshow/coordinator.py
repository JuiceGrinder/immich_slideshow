"""Data update coordinator for Immich Slideshow."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_API_KEY, CONF_SERVER_URL, CONF_ALBUM_ID, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN
from .immich_client import ImmichClient

_LOGGER = logging.getLogger(__name__)

class ImmichDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Immich data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        if not entry.data:
            _LOGGER.error("Config entry has no data")
            raise ValueError("Config entry data is empty")
            
        _LOGGER.debug("Initializing coordinator with entry data keys: %s", list(entry.data.keys()))
        _LOGGER.debug("Entry data: %s", {k: "***" if "key" in k.lower() or "token" in k.lower() else v for k, v in entry.data.items()})
        
        # Handle various possible key formats for backward compatibility
        server_url = (entry.data.get(CONF_SERVER_URL) or 
                     entry.data.get("url") or 
                     entry.data.get("server") or
                     entry.data.get("host") or
                     entry.data.get("base_url"))
        
        api_key = (entry.data.get(CONF_API_KEY) or 
                  entry.data.get("API_KEY") or  # Handle uppercase
                  entry.data.get("key") or 
                  entry.data.get("api_token") or
                  entry.data.get("token") or
                  entry.data.get("access_token"))
        
        # Handle the case where server URL might be stored as a key instead of value
        # Look for keys that look like URLs
        if not server_url:
            for key in entry.data.keys():
                if (key.startswith('http://') or key.startswith('https://')) and '.' in key:
                    server_url = key
                    _LOGGER.warning("Found server URL stored as key instead of value: %s", server_url)
                    break
        
        # Handle album_id with various case formats
        album_id = (entry.data.get(CONF_ALBUM_ID) or 
                   entry.data.get("Album_ID") or
                   entry.data.get("album_id") or
                   entry.data.get("ALBUM_ID"))
        
        if not server_url:
            _LOGGER.error("Server URL not found in config data. Available keys: %s", list(entry.data.keys()))
            _LOGGER.error("Full entry data (sanitized): %s", {k: "***" if "key" in k.lower() or "token" in k.lower() else v for k, v in entry.data.items()})
            raise ValueError(f"Server URL not found in config data. Available keys: {list(entry.data.keys())}")
        if not api_key:
            _LOGGER.error("API Key not found in config data. Available keys: %s", list(entry.data.keys()))
            _LOGGER.error("Full entry data (sanitized): %s", {k: "***" if "key" in k.lower() or "token" in k.lower() else v for k, v in entry.data.items()})
            raise ValueError(f"API Key not found in config data. Available keys: {list(entry.data.keys())}")
            
        self.client = ImmichClient(server_url, api_key)
        self.album_id = album_id
        self.image_history = []  # Track last 10 images
        self.history_index = -1  # Current position in history (-1 = live mode)
        
        # Get interval from options first, then data, then default
        update_interval = entry.options.get(
            CONF_UPDATE_INTERVAL,
            entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        )
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
            # Reduce initial refresh timeout to fail faster if there are issues
            request_refresh_debouncer=None,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Immich."""
        try:
            assets = await self.hass.async_add_executor_job(
                self.client.get_album_assets, self.album_id
            )
            
            if not assets:
                return {"assets": [], "current_index": 0}
            
            current_data = self.data or {"current_index": 0}
            current_index = current_data.get("current_index", 0)
            
            # Auto-advance to next image on each update (slideshow behavior)
            # Only advance if in live mode (history_index == -1) and not first load
            if self.data and self.history_index == -1:
                current_index = (current_index + 1) % len(assets)
                # Add current image to history when advancing
                if assets and current_index < len(assets):
                    self._add_to_history(assets[current_index])
            
            if current_index >= len(assets):
                current_index = 0
            
            current_asset = assets[current_index] if assets else None
            
            return {
                "assets": assets,
                "current_index": current_index,
                "current_asset": current_asset,
                "history_index": self.history_index,
                "in_live_mode": self.history_index == -1,
            }
            
        except Exception as exc:
            raise UpdateFailed(f"Error communicating with Immich API: {exc}") from exc

    def _add_to_history(self, asset: dict[str, Any]) -> None:
        """Add an asset to history, keeping only last 10."""
        # Remove if already in history to avoid duplicates
        self.image_history = [h for h in self.image_history if h.get("id") != asset.get("id")]
        # Add to beginning
        self.image_history.insert(0, asset)
        # Keep only last 10
        if len(self.image_history) > 10:
            self.image_history = self.image_history[:10]

    async def async_next_image(self) -> None:
        """Move to next image (async version)."""
        if not self.data or not self.data.get("assets"):
            return
            
        assets = self.data["assets"]
        
        if self.history_index == -1:
            # In live mode, advance normally
            current_index = self.data.get("current_index", 0)
            current_index = (current_index + 1) % len(assets)
            
            self.data["current_index"] = current_index
            self.data["current_asset"] = assets[current_index]
            
            # Add to history
            self._add_to_history(assets[current_index])
        else:
            # In history mode, move forward in history or back to live
            if self.history_index > 0:
                self.history_index -= 1
                self.data["current_asset"] = self.image_history[self.history_index]
            else:
                # Back to live mode
                self.history_index = -1
                current_index = self.data.get("current_index", 0)
                self.data["current_asset"] = assets[current_index]
        
        self.data["history_index"] = self.history_index
        self.data["in_live_mode"] = self.history_index == -1
        self.async_set_updated_data(self.data)

    async def async_previous_image(self) -> None:
        """Move to previous image (navigate history)."""
        if not self.data or not self.image_history:
            return
            
        if self.history_index == -1:
            # Enter history mode from live mode
            self.history_index = 0
        else:
            # Go further back in history
            self.history_index = min(self.history_index + 1, len(self.image_history) - 1)
            
        if self.history_index < len(self.image_history):
            self.data["current_asset"] = self.image_history[self.history_index]
            self.data["history_index"] = self.history_index
            self.data["in_live_mode"] = False
            self.async_set_updated_data(self.data)

    def next_image(self) -> None:
        """Move to next image (sync version for backward compatibility)."""
        if not self.data or not self.data.get("assets"):
            return
            
        current_index = self.data.get("current_index", 0)
        assets = self.data["assets"]
        
        current_index = (current_index + 1) % len(assets)
        
        self.data["current_index"] = current_index
        self.data["current_asset"] = assets[current_index]
        
        # Don't call async_set_updated_data from sync method
        # The service handler will call the async version instead