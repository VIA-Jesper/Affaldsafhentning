"""Config flow for Affaldsafhentning integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_PICKUP_DAY,
    CONF_PICKUP_FREQUENCY,
    CONF_START_WEEK,
    CONF_WASTE_TYPE,
    CONF_EXCEPTIONS,
)

_LOGGER = logging.getLogger(__name__)

# Weekday mapping for selection
WEEKDAYS_OPTIONS = {
    0: "Mandag",
    1: "Tirsdag",
    2: "Onsdag",
    3: "Torsdag",
    4: "Fredag",
    5: "Lørdag",
    6: "Søndag",
}

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Affaldsafhentning."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_WASTE_TYPE], 
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_WASTE_TYPE): str,
                    vol.Required(CONF_PICKUP_FREQUENCY, default=2): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=52)
                    ),
                    vol.Required(CONF_PICKUP_DAY, default=0): vol.In(WEEKDAYS_OPTIONS),
                    vol.Required(CONF_START_WEEK, default=1): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=53)
                    ),
                }
            ),
            errors=errors,
        )

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Affaldsafhentning."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_EXCEPTIONS,
                        default=self.config_entry.options.get(CONF_EXCEPTIONS, ""),
                    ): str,
                }
            ),
        )
