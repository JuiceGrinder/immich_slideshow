"""Camera platform for Immich Slideshow."""
from __future__ import annotations

import logging
from typing import Any
import requests
from PIL import Image
import io

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
        self._image_cache = {}  # Cache keyed by (asset_id, width, height)

    @property
    def is_on(self) -> bool:
        """Return true if the camera is on."""
        return self.coordinator.data is not None and len(self.coordinator.data.get("assets", [])) > 0

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image."""
        _LOGGER.error("IMMICH DEBUG: Camera image requested with dimensions: %sx%s", width, height)
        
        if not self.coordinator.data:
            _LOGGER.warning("No coordinator data available")
            return None
            
        if not self.coordinator.data.get("current_asset"):
            _LOGGER.warning("No current asset in coordinator data. Available keys: %s", 
                           list(self.coordinator.data.keys()) if self.coordinator.data else [])
            return None
            
        current_asset = self.coordinator.data["current_asset"]
        current_asset_id = current_asset.get("id")
        
        # Create cache key including dimensions for proper caching of resized images
        cache_key = (current_asset_id, width, height)
        
        # Check if we have this specific sized image cached
        if cache_key in self._image_cache:
            _LOGGER.debug("Returning cached image for asset %s (%sx%s)", current_asset_id, width, height)
            return self._image_cache[cache_key]
        
        _LOGGER.debug("Fetching new image for asset: %s", current_asset_id)
        
        try:
            # Use thumbnail for faster loading by default, can be configured
            from .const import (CONF_USE_THUMBNAILS, DEFAULT_USE_THUMBNAILS, 
                               CONF_RESPECT_CARD_SIZE, DEFAULT_RESPECT_CARD_SIZE,
                               CONF_CROP_TO_FIT, DEFAULT_CROP_TO_FIT)
            use_thumbnails = self._entry.options.get(CONF_USE_THUMBNAILS, DEFAULT_USE_THUMBNAILS)
            respect_card_size = self._entry.options.get(CONF_RESPECT_CARD_SIZE, DEFAULT_RESPECT_CARD_SIZE)
            crop_to_fit = self._entry.options.get(CONF_CROP_TO_FIT, DEFAULT_CROP_TO_FIT)
            
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
            
            image_data = response.content
            
            # Resize image if card dimensions are provided and respect_card_size is enabled
            if respect_card_size and (width or height):
                _LOGGER.error("IMMICH DEBUG: Card dimensions provided: width=%s, height=%s, respect_card_size=%s, crop_to_fit=%s", 
                            width, height, respect_card_size, crop_to_fit)
                image_data = await self.hass.async_add_executor_job(
                    self._resize_image, image_data, width, height, crop_to_fit
                )
            
            # Cache the processed image data
            self._image_cache[cache_key] = image_data
            
            # Limit cache size to prevent memory issues (keep last 10 images)
            if len(self._image_cache) > 10:
                # Remove oldest entries (this is a simple approach, could use LRU)
                oldest_keys = list(self._image_cache.keys())[:-10]
                for old_key in oldest_keys:
                    del self._image_cache[old_key]
            
            _LOGGER.debug("Successfully fetched and cached image (%sx%s), size: %d bytes", 
                         width, height, len(image_data))
            return image_data
            
        except Exception as exc:
            _LOGGER.error("Failed to fetch image from %s: %s", image_url, exc)
            return None

    def _resize_image(self, image_data: bytes, width: int | None = None, height: int | None = None, crop_to_fit: bool = False) -> bytes:
        """Resize image to fit the requested dimensions while maintaining aspect ratio."""
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                original_width, original_height = img.size
                aspect_ratio = original_width / original_height
                is_vertical = aspect_ratio < 1.0
                
                _LOGGER.error("IMMICH DEBUG: Resize request: original=%dx%d, target=%sx%s, aspect=%.2f, vertical=%s", 
                            original_width, original_height, width or "auto", height or "auto", 
                            aspect_ratio, is_vertical)
                
                if not width and not height:
                    # No resize needed
                    _LOGGER.debug("No dimensions specified, returning original image")
                    return image_data
                
                # Apply reasonable defaults for common card scenarios
                if width and not height and is_vertical:
                    # For vertical images with only width, infer a reasonable height based on common card ratios
                    # Most cards have a 16:9 or 4:3 aspect ratio
                    inferred_height = int(width * 0.75)  # 4:3 ratio
                    _LOGGER.info("Vertical image with only width specified, inferring height: %d", inferred_height)
                    height = inferred_height
                
                # Calculate scale factors
                scale_width = width / original_width if width else float('inf')
                scale_height = height / original_height if height else float('inf')
                
                _LOGGER.error("IMMICH DEBUG: Scale factors: width_scale=%.3f, height_scale=%.3f", scale_width, scale_height)
                
                # Use the smaller scale to ensure image fits within both constraints
                scale = min(scale_width, scale_height)
                
                _LOGGER.error("IMMICH DEBUG: Selected scale: %.3f", scale)
                
                # Ensure we don't upscale beyond reasonable limits
                if scale > 2.0:
                    scale = min(scale, 2.0)
                    _LOGGER.debug("Limiting upscale to 2.0x for quality preservation")
                
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                
                # Ensure minimum size
                if new_width < 10 or new_height < 10:
                    _LOGGER.warning("Calculated size too small (%dx%d), using minimum 10x10", new_width, new_height)
                    new_width = max(new_width, 10)
                    new_height = max(new_height, 10)
                
                _LOGGER.error("IMMICH DEBUG: Final dimensions: %dx%d (scale: %.3f) - fits in %dx%d? width=%s height=%s", 
                             new_width, new_height, scale, width or 0, height or 0,
                             new_width <= (width or 9999), new_height <= (height or 9999))
                
                # Only resize if the new dimensions are significantly different
                if abs(new_width - original_width) < 10 and abs(new_height - original_height) < 10:
                    _LOGGER.debug("New size very close to original, skipping resize")
                    return image_data
                
                # For crop_to_fit mode, we need different logic
                if crop_to_fit and width and height:
                    _LOGGER.error("IMMICH DEBUG: Using crop-to-fit mode for exact %dx%d dimensions", width, height)
                    
                    # First, scale the image to fill the target area (one dimension will match, other will be larger)
                    target_aspect = width / height
                    source_aspect = original_width / original_height
                    
                    if source_aspect > target_aspect:
                        # Image is wider than target - scale by height, then crop width
                        temp_height = height
                        temp_width = int(original_width * (height / original_height))
                    else:
                        # Image is taller than target - scale by width, then crop height  
                        temp_width = width
                        temp_height = int(original_height * (width / original_width))
                    
                    _LOGGER.error("IMMICH DEBUG: Crop step 1 - scale to %dx%d", temp_width, temp_height)
                    
                    # Scale the image to temporary size
                    temp_img = img.resize((temp_width, temp_height), Image.Resampling.LANCZOS)
                    
                    # Now crop to exact target size from center
                    left = (temp_width - width) // 2
                    top = (temp_height - height) // 2
                    right = left + width
                    bottom = top + height
                    
                    _LOGGER.error("IMMICH DEBUG: Crop step 2 - crop from (%d,%d) to (%d,%d)", left, top, right, bottom)
                    
                    resized_img = temp_img.crop((left, top, right, bottom))
                    new_width, new_height = width, height  # Update for logging
                else:
                    # Standard resize maintaining aspect ratio
                    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert back to bytes
                output = io.BytesIO()
                # Preserve original format if possible, otherwise use JPEG
                format_to_use = img.format if img.format in ['JPEG', 'PNG', 'WEBP'] else 'JPEG'
                
                # Adjust quality based on the scale factor to balance size and quality
                quality = 85
                if scale < 0.5:  # Significant downscaling
                    quality = 90  # Higher quality for small images
                elif scale > 1.5:  # Upscaling
                    quality = 80  # Lower quality for upscaled images
                
                resized_img.save(output, format=format_to_use, quality=quality, optimize=True)
                resized_data = output.getvalue()
                _LOGGER.error("IMMICH DEBUG: Resize complete - original size: %d bytes, resized size: %d bytes", 
                             len(image_data), len(resized_data))
                return resized_data
                
        except Exception as exc:
            _LOGGER.error("Failed to resize image: %s", exc)
            # Return original image data if resize fails
            return image_data

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