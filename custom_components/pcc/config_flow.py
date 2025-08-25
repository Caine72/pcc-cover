from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_FRIENDLY_NAME,
    CONF_UNIQUE_ID,
    CONF_VALUE_TEMPLATE,
)
from homeassistant.core import callback
from homeassistant.helpers import selector as sel

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

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


def _schema(defaults: dict[str, Any] | None = None, include_unique: bool = True) -> vol.Schema:
    """Return the schema for initial setup (include_unique=True) or OptionsFlow (False)."""
    d = defaults or {}

    schema: dict[Any, Any] = {
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
    }

    if include_unique:
        # unique_id is immutable; only present for the initial setup form
        schema[vol.Required(CONF_UNIQUE_ID, default=d.get(CONF_UNIQUE_ID, ""))] = sel.selector({"text": {}})

    return vol.Schema(schema)


class PCCConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for PCC (one cover per entry)."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        _LOGGER.debug("PCC: async_step_user (received_input=%s)", user_input is not None)
        errors: dict[str, str] = {}

        if user_input is not None:
            existing_ids = [e.unique_id for e in self._async_current_entries()]
            if user_input[CONF_UNIQUE_ID] in existing_ids:
                errors[CONF_UNIQUE_ID] = "duplicate_unique_id"
                _LOGGER.debug("PCC: duplicate unique_id: %s", user_input[CONF_UNIQUE_ID])

            if not errors:
                _LOGGER.debug(
                    "PCC: creating entry title=%r unique_id=%r",
                    user_input.get(CONF_FRIENDLY_NAME), user_input.get(CONF_UNIQUE_ID)
                )
                return self.async_create_entry(
                    title=user_input[CONF_FRIENDLY_NAME],
                    data=user_input,
                )

        _LOGGER.debug("PCC: showing initial setup form (includes unique_id)")
        return self.async_show_form(step_id="user", data_schema=_schema(include_unique=True), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Expose the OptionsFlow so 'Configure' appears on the integration card."""
        _LOGGER.debug("PCC: async_get_options_flow for entry_id=%s", getattr(config_entry, "entry_id", "?"))
        return PCCOptionsFlow(config_entry)


class PCCOptionsFlow(config_entries.OptionsFlow):
    """Options flow for post-setup configuration (does not allow changing unique_id)."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry
        _LOGGER.debug("PCC: OptionsFlow __init__ entry_id=%s", config_entry.entry_id)

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            _LOGGER.debug("PCC: options saved entry_id=%s", self.config_entry.entry_id)
            return self.async_create_entry(title="", data=user_input)

        defaults = {**self.config_entry.data, **self.config_entry.options}
        _LOGGER.debug("PCC: options form opened entry_id=%s", self.config_entry.entry_id)

        schema = _schema({
            **defaults,
            # Use entry.title as a sensible fallback for friendly name
            CONF_FRIENDLY_NAME: defaults.get(CONF_FRIENDLY_NAME, self.config_entry.title),
        }, include_unique=False)

        _LOGGER.debug("PCC: showing options form (exclude unique_id) entry_id=%s", self.config_entry.entry_id)
        return self.async_show_form(step_id="init", data_schema=schema)
