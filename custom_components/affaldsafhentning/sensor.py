"""Sensor platform for Affaldsafhentning."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN,
    CONF_PICKUP_DAY,
    CONF_PICKUP_FREQUENCY,
    CONF_START_WEEK,
    CONF_WASTE_TYPE,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    config = entry.data
    
    # Note: If the user wants multiple types, they currently add multiple config entries
    # or we could adjust the flow to allow multiple sensors in one entry.
    # For simplicity in this initial version, one config entry = one type.
    
    async_add_entities([AffaldSensor(hass, entry)], True)

class AffaldSensor(SensorEntity):
    """Representation of an Affaldsafhentning sensor."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._hass = hass
        self._entry = entry
        
        # Store raw waste type for logic and attributes
        self._waste_type = entry.data.get(CONF_WASTE_TYPE)
        
        # Prefix the name for easier finding in Home Assistant
        self._attr_name = f"Affaldsafhentning {self._waste_type}"
        self._attr_unique_id = f"{entry.entry_id}_pickup"
        
        self._pickup_day = entry.data.get(CONF_PICKUP_DAY)
        self._frequency = entry.data.get(CONF_PICKUP_FREQUENCY)
        self._start_week = entry.data.get(CONF_START_WEEK)
        
        self._state: datetime | None = None
        self._days_until: int | None = None

    @property
    def state(self) -> StateType:
        """Return the state of the sensor (next pickup date)."""
        if self._state:
            return self._state.strftime("%Y-%m-%d")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return the state attributes."""
        is_today = False
        is_tomorrow = False
        
        if self._state:
            today = datetime.now().date()
            is_today = self._state == today
            is_tomorrow = self._state == (today + timedelta(days=1))

        human_readable = f"Om {self._days_until} dage"
        if self._days_until == 0:
            human_readable = "I dag"
        elif self._days_until == 1:
            human_readable = "I morgen"

        return {
            "days_until_pickup": self._days_until,
            "human_readable_next": human_readable,
            "is_today": is_today,
            "is_tomorrow": is_tomorrow,
            "pickup_frequency": self._frequency,
            "pickup_day": self._pickup_day,
            "collection_of": self._waste_type,
        }

    @property
    def entity_picture(self) -> str | None:
        """Return the entity picture."""
        # Map common waste types to the actual pictogram filenames
        name = self._waste_type.lower()
        
        mapping = {
            "rest": "restaffald",
            "mad": "madaffald",
            "plast": "plast",
            "glas": "glas",
            "metal": "metal",
            "papir": "papir",
            "pap": "pap",
            "tekstil": "tekstilaffald",
            "karton": "mad_og_drikkekartoner",
            "farligt": "farligt_affald",
            "hård plast": "haard_plast",
            "blød plast": "bloed_plast_2",
        }
        
        found_images = []
        
        # Iterate through mapping to find all matches
        for key, value in mapping.items():
            if key in name:
                # Avoid duplicates (e.g. dont add 'plast' again if 'hård plast' was found)
                # Simple check: if we have a match, add it.
                # But 'plast' is inside 'hård plast'. To avoid double match, one could be more clever.
                # For now, simple set logic or list check.
                if value not in found_images:
                    found_images.append(value)
        
        # Specific cleanup: if 'haard_plast' or 'bloed_plast_2' is present, remove generic 'plast' if present
        if "plast" in found_images:
            if "haard_plast" in found_images or "bloed_plast_2" in found_images:
                found_images.remove("plast")

        if not found_images:
             # Default
            image_name = "restaffald"
            return f"/api/affaldsafhentning/icons/{image_name}.jpg"
            
        if len(found_images) == 1:
            return f"/api/affaldsafhentning/icons/{found_images[0]}.jpg"
            
        # If multiple images, use dynamic API
        images_str = ",".join(found_images)
        return f"/api/affaldsafhentning/image?images={images_str}"

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        now = datetime.now()
        today = now.date()
        
        # We find the next pickup date by checking upcoming weeks
        # Current Monday
        monday_this_week = today - timedelta(days=today.weekday())
        
        found = False
        # Look ahead up to 52 weeks
        for week_offset in range(53):
            target_date_monday = monday_this_week + timedelta(weeks=week_offset)
            target_date_pickup = target_date_monday + timedelta(days=self._pickup_day)
            
            # Skip if the pickup day in this week is already in the past
            if target_date_pickup < today:
                continue
                
            # Check if this week is a pickup week
            # ISO week number for the target date
            _, check_week, _ = target_date_pickup.isocalendar()
            
            weeks_since_start = (check_week - self._start_week) % self._frequency
            
            if weeks_since_start == 0:
                final_date = target_date_pickup
                
                # Check for manual overrides in options
                exceptions_str = self._entry.options.get("exceptions", "")
                if exceptions_str:
                    # Format: 2024-12-24:2024-12-27, 2025-01-01:2025-01-02
                    try:
                        exceptions = {}
                        for pair in exceptions_str.replace(" ", "").split(","):
                            if ":" in pair:
                                old, new = pair.split(":")
                                exceptions[old] = new
                        
                        date_key = final_date.strftime("%Y-%m-%d")
                        if date_key in exceptions:
                            final_date = datetime.strptime(exceptions[date_key], "%Y-%m-%d").date()
                            _LOGGER.debug("Overriding pickup date for %s: %s -> %s", self._attr_name, date_key, final_date)
                    except Exception as e:
                        _LOGGER.warning("Could not parse exceptions for %s: %s", self._attr_name, e)

                self._state = final_date
                self._days_until = (final_date - today).days
                found = True
                break
        
        if not found:
            _LOGGER.error("Kunne ikke finde næste afhentningsdato for %s", self._attr_name)
