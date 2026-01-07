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
