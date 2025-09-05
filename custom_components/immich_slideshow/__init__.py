"""The Immich Slideshow integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .coordinator import ImmichDataUpdateCoordinator

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Immich Slideshow integration."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Immich Slideshow from a config entry."""
    coordinator = ImmichDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Set up options update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    async def handle_next_image(call):
        """Handle the next_image service call."""
        # Call async_next_image on all coordinators (usually just one)
        for coord in hass.data[DOMAIN].values():
            if hasattr(coord, 'async_next_image'):
                await coord.async_next_image()

    async def handle_previous_image(call):
        """Handle the previous_image service call."""
        # Call async_previous_image on all coordinators (usually just one)
        for coord in hass.data[DOMAIN].values():
            if hasattr(coord, 'async_previous_image'):
                await coord.async_previous_image()
    
    hass.services.async_register(DOMAIN, "next_image", handle_next_image)
    hass.services.async_register(DOMAIN, "previous_image", handle_previous_image)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        # Remove services if this was the last entry
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "next_image")
            hass.services.async_remove(DOMAIN, "previous_image")
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)