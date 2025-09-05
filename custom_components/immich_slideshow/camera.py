"""Camera platform for Immich Slideshow."""
from __future__ import annotations

import logging
from typing import Any
import requests

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ImmichDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Immich Slideshow camera based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([ImmichSlideshowCamera(coordinator, entry)])

class ImmichSlideshowCamera(CoordinatorEntity, Camera):
    """Representation of an Immich Slideshow camera."""

    def __init__(
        self,
        coordinator: ImmichDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the camera."""
        super().__init__(coordinator)
        Camera.__init__(self)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_slideshow_camera"
        self._attr_name = "Immich Slideshow"
        self._attr_icon = "mdi:camera"
        self._cached_image_data = None
        self._cached_asset_id = None

    @property
    def is_on(self) -> bool:
        """Return true if the camera is on."""
        return self.coordinator.data is not None and len(self.coordinator.data.get("assets", [])) > 0

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image."""
        _LOGGER.debug("Camera image requested - coordinator data: %s", bool(self.coordinator.data))
        
        if not self.coordinator.data:
            _LOGGER.warning("No coordinator data available")
            return None
            
        if not self.coordinator.data.get("current_asset"):
            _LOGGER.warning("No current asset in coordinator data. Available keys: %s", 
                           list(self.coordinator.data.keys()) if self.coordinator.data else [])
            return None
            
        current_asset = self.coordinator.data["current_asset"]
        current_asset_id = current_asset.get("id")
        
        # Check if we have this image cached
        if self._cached_asset_id == current_asset_id and self._cached_image_data:
            _LOGGER.debug("Returning cached image for asset: %s", current_asset_id)
            return self._cached_image_data
        
        _LOGGER.debug("Fetching new image for asset: %s", current_asset_id)
        
        try:
            # Use thumbnail for faster loading by default, can be configured
            from .const import CONF_USE_THUMBNAILS, DEFAULT_USE_THUMBNAILS
            use_thumbnails = self._entry.options.get(CONF_USE_THUMBNAILS, DEFAULT_USE_THUMBNAILS)
            
            if use_thumbnails:
                image_url = self.coordinator.client.get_asset_thumbnail_url(current_asset_id, "preview")
                _LOGGER.debug("Thumbnail URL: %s", image_url)
            else:
                image_url = self.coordinator.client.get_asset_download_url(current_asset_id)
                _LOGGER.debug("Original image URL: %s", image_url)
            
            response = await self.hass.async_add_executor_job(
                lambda: requests.get(
                    image_url, 
                    timeout=10,  # Reduced timeout since thumbnails are faster
                    headers=self.coordinator.client.headers
                )
            )
            response.raise_for_status()
            
            # Cache the image data
            self._cached_image_data = response.content
            self._cached_asset_id = current_asset_id
            
            _LOGGER.debug("Successfully fetched and cached image, size: %d bytes", len(response.content))
            return response.content
            
        except Exception as exc:
            _LOGGER.error("Failed to fetch image from %s: %s", image_url, exc)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the camera state attributes."""
        if not self.coordinator.data or not self.coordinator.data.get("current_asset"):
            return None
            
        current_asset = self.coordinator.data["current_asset"]
        
        return {
            "current_image_id": current_asset.get("id"),
            "filename": current_asset.get("originalFileName", "Unknown"),
            "current_index": self.coordinator.data.get("current_index", 0),
            "total_images": len(self.coordinator.data.get("assets", [])),
            "image_url": self.coordinator.client.get_asset_download_url(current_asset["id"]),
            "thumbnail_url": self.coordinator.client.get_asset_thumbnail_url(current_asset["id"]),
            "in_live_mode": self.coordinator.data.get("in_live_mode", True),
            "history_index": self.coordinator.data.get("history_index", -1),
            "history_length": len(self.coordinator.image_history),
            "navigation_mode": "Live" if self.coordinator.data.get("in_live_mode", True) else f"History {self.coordinator.data.get('history_index', 0) + 1}/{len(self.coordinator.image_history)}",
        }