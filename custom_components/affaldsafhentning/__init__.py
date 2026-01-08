"""The Affaldsafhentning integration."""
from __future__ import annotations

import os
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Affaldsafhentning from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Register static path for icons if not already done
    if "static_registered" not in hass.data[DOMAIN]:
        icon_path = os.path.join(os.path.dirname(__file__), "icons")
        if not os.path.exists(icon_path):
            os.makedirs(icon_path)
            
        await hass.http.async_register_static_paths(
            [StaticPathConfig("/api/affaldsafhentning/icons", icon_path, cache_headers=True)]
        )
        hass.data[DOMAIN]["static_registered"] = True

    # Store settings for this entry
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # Register dynamic image view
    hass.http.register_view(AffaldImageHandler(hass))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

from homeassistant.components.http import HomeAssistantView
from aiohttp import web
from PIL import Image
import io

class AffaldImageHandler(HomeAssistantView):
    """View to handle dynamic waste icon generation."""

    url = "/api/affaldsafhentning/image"
    name = "api:affaldsafhentning:image"
    requires_auth = False

    def __init__(self, hass):
        """Initialize user view."""
        self.hass = hass
        self.icon_dir = os.path.join(os.path.dirname(__file__), "icons")

    async def get(self, request):
        """Handle get request for dynamic image."""
        images_param = request.query.get("images")
        if not images_param:
            return web.Response(status=400, text="Missing images parameter")

        image_names = images_param.split(",")
        
        try:
            image_data = await self.hass.async_add_executor_job(
                self._generate_image, image_names
            )
        except ValueError:
            return web.Response(status=404, text="No valid images found")
        except Exception as e:
            return web.Response(status=500, text=str(e))

        return web.Response(body=image_data, content_type="image/png")

    def _generate_image(self, image_names):
        """Generate the combined image in a thread."""
        images = []
        
        # Load all requested images
        for name in image_names:
            # Sanitize filename to prevent path traversal
            clean_name = os.path.basename(name)
            path = os.path.join(self.icon_dir, f"{clean_name}.jpg")
            if os.path.exists(path):
                images.append(Image.open(path))
        
        if not images:
            raise ValueError("No valid images found")
            
        if len(images) == 1:
            # If only one image valid, serve it directly (convert to bytes)
            img_byte_arr = io.BytesIO()
            images[0].save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()

        # Combine images side-by-side
        # Assume all images are roughly same height, or resize to match first
        base_height = images[0].height
        
        # Resize all to match base height
        resized_images = []
        for img in images:
            if img.height != base_height:
                ratio = base_height / img.height
                new_width = int(img.width * ratio)
                resized_images.append(img.resize((new_width, base_height)))
            else:
                resized_images.append(img)
                
        total_width = sum(img.width for img in resized_images)
        
        # Create new image with transparent background
        combined_image = Image.new('RGBA', (total_width, base_height), (0, 0, 0, 0))
        
        x_offset = 0
        for img in resized_images:
            combined_image.paste(img, (x_offset, 0))
            x_offset += img.width
            
        img_byte_arr = io.BytesIO()
        combined_image.save(img_byte_arr, format='PNG')
        
        return img_byte_arr.getvalue()
