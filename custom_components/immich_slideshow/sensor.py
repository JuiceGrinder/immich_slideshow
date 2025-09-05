"""Sensor platform for Immich Slideshow."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
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
    """Set up Immich Slideshow sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([
        ImmichCurrentImageSensor(coordinator, entry),
        ImmichImageCountSensor(coordinator, entry),
        ImmichNextImageService(coordinator, entry),
    ])

class ImmichCurrentImageSensor(CoordinatorEntity, SensorEntity):
    """Representation of the current image sensor."""

    def __init__(
        self,
        coordinator: ImmichDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_current_image"
        self._attr_name = "Immich Current Image"
        self._attr_icon = "mdi:image"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if not self.coordinator.data or not self.coordinator.data.get("current_asset"):
            return None
        
        current_asset = self.coordinator.data["current_asset"]
        return current_asset.get("id")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if not self.coordinator.data or not self.coordinator.data.get("current_asset"):
            return None
            
        current_asset = self.coordinator.data["current_asset"]
        
        return {
            "image_url": self.coordinator.client.get_asset_download_url(current_asset["id"]),
            "thumbnail_url": self.coordinator.client.get_asset_thumbnail_url(current_asset["id"]),
            "filename": current_asset.get("originalFileName", "Unknown"),
            "file_created_at": current_asset.get("fileCreatedAt"),
            "file_modified_at": current_asset.get("fileModifiedAt"),
            "device_id": current_asset.get("deviceId"),
            "type": current_asset.get("type"),
            "current_index": self.coordinator.data.get("current_index", 0),
            "total_images": len(self.coordinator.data.get("assets", [])),
        }

class ImmichImageCountSensor(CoordinatorEntity, SensorEntity):
    """Representation of the image count sensor."""

    def __init__(
        self,
        coordinator: ImmichDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_image_count"
        self._attr_name = "Immich Image Count"
        self._attr_icon = "mdi:counter"
        self._attr_native_unit_of_measurement = "images"

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return 0
        return len(self.coordinator.data.get("assets", []))

class ImmichNextImageService(CoordinatorEntity, SensorEntity):
    """Service to advance to next image."""

    def __init__(
        self,
        coordinator: ImmichDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the service sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_next_image_service"
        self._attr_name = "Immich Next Image"
        self._attr_icon = "mdi:skip-next"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return "ready"

    async def async_next_image(self) -> None:
        """Advance to next image."""
        await self.hass.async_add_executor_job(self.coordinator.next_image)