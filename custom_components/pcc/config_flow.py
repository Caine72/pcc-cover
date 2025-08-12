from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_UNIQUE_ID,
    CONF_FRIENDLY_NAME,
    CONF_DEVICE_CLASS,
    CONF_VALUE_TEMPLATE,
)
from homeassistant.helpers import selector as sel
from typing import Any
from . import DOMAIN

CONF_OPEN_COVER = "open_cover"
CONF_CLOSE_COVER = "close_cover"
CONF_STOP_COVER = "stop_cover"
CONF_TRAVEL_UP = "travelling_time_up"
CONF_TRAVEL_DOWN = "travelling_time_down"

DEFAULT_TRAVEL_TIME = 25
DEVICE_CLASSES = [
    "awning", "blind", "curtain", "damper", "door", "garage", "gate",
    "shade", "shutter", "window",
]


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema({

        vol.Required(CONF_UNIQUE_ID, default=d.get(CONF_UNIQUE_ID, "")): sel.selector({"text": {}}),
        vol.Required(CONF_FRIENDLY_NAME, default=d.get(CONF_FRIENDLY_NAME, "")): sel.selector({"text": {}}),

        vol.Optional(CONF_DEVICE_CLASS, default=d.get(CONF_DEVICE_CLASS)): sel.selector({
            "select": {"options": DEVICE_CLASSES, "mode": "dropdown", "multiple": False, "sort": True}
        }),

        vol.Required(CONF_VALUE_TEMPLATE, default=d.get(CONF_VALUE_TEMPLATE, "")): sel.selector({"template": {}}),

        vol.Required(CONF_OPEN_COVER, default=d.get(CONF_OPEN_COVER, [])): sel.selector({"action": {}}),
        vol.Required(CONF_CLOSE_COVER, default=d.get(CONF_CLOSE_COVER, [])): sel.selector({"action": {}}),
        vol.Optional(CONF_STOP_COVER, default=d.get(CONF_STOP_COVER, [])): sel.selector({"action": {}}),

        vol.Optional(CONF_TRAVEL_UP, default=d.get(CONF_TRAVEL_UP, DEFAULT_TRAVEL_TIME)):
            sel.selector({"number": {"min": 1, "max": 600, "mode": "box"}}),
        vol.Optional(CONF_TRAVEL_DOWN, default=d.get(CONF_TRAVEL_DOWN, DEFAULT_TRAVEL_TIME)):
            sel.selector({"number": {"min": 1, "max": 600, "mode": "box"}}),
    })


class PCCConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PCC (one cover per entry)."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            existing_ids = [e.unique_id for e in self._async_current_entries()]
            if user_input[CONF_UNIQUE_ID] in existing_ids:
                errors[CONF_UNIQUE_ID] = "duplicate_unique_id"

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_FRIENDLY_NAME],
                    data=user_input,
                )

        return self.async_show_form(step_id="user", data_schema=_schema(), errors=errors)


class PCCOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        defaults = {**self.entry.data, **self.entry.options}
        schema = _schema({
            **defaults,
            CONF_UNIQUE_ID: defaults.get(CONF_UNIQUE_ID, self.entry.unique_id or ""),
            CONF_FRIENDLY_NAME: defaults.get(CONF_FRIENDLY_NAME, self.entry.title),
        })
        return self.async_show_form(step_id="init", data_schema=schema)

async def async_get_options_flow(config_entry):
    return PCCOptionsFlow(config_entry)

