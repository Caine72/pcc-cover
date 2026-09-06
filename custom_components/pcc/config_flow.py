import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_FRIENDLY_NAME,
    CONF_UNIQUE_ID,
    CONF_VALUE_TEMPLATE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import selector as sel
from homeassistant.helpers.template import Template

from .const import (
    CONF_CLOSE_COVER,
    CONF_OPEN_COVER,
    CONF_STOP_COVER,
    CONF_TRAVEL_DOWN,
    CONF_TRAVEL_UP,
    DEFAULT_TRAVEL_TIME,
    DEVICE_CLASSES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _schema(
    defaults: dict[str, Any] | None = None,
    include_unique: bool = True,
) -> vol.Schema:
    """Return the schema for initial setup (include_unique=True) or OptionsFlow (False)."""
    d = defaults or {}
    device_class_key = (
        vol.Optional(CONF_DEVICE_CLASS, default=d[CONF_DEVICE_CLASS])
        if d.get(CONF_DEVICE_CLASS)
        else vol.Optional(CONF_DEVICE_CLASS)
    )

    schema: dict[Any, Any] = {
        vol.Required(
            CONF_FRIENDLY_NAME,
            default=d.get(CONF_FRIENDLY_NAME, ""),
        ): sel.selector({"text": {}}),
        device_class_key: sel.selector(
            {
                "select": {
                    "options": DEVICE_CLASSES,
                    "mode": "dropdown",
                    "multiple": False,
                    "sort": True,
                }
            }
        ),
        vol.Required(
            CONF_VALUE_TEMPLATE,
            default=d.get(CONF_VALUE_TEMPLATE, ""),
        ): sel.selector({"template": {}}),
        vol.Required(
            CONF_OPEN_COVER,
            default=d.get(CONF_OPEN_COVER, []),
        ): sel.selector({"action": {}}),
        vol.Required(
            CONF_CLOSE_COVER,
            default=d.get(CONF_CLOSE_COVER, []),
        ): sel.selector({"action": {}}),
        vol.Optional(
            CONF_STOP_COVER,
            default=d.get(CONF_STOP_COVER, []),
        ): sel.selector({"action": {}}),
        vol.Optional(
            CONF_TRAVEL_UP,
            default=d.get(CONF_TRAVEL_UP, DEFAULT_TRAVEL_TIME),
        ): sel.selector({"number": {"min": 1, "max": 600, "mode": "box"}}),
        vol.Optional(
            CONF_TRAVEL_DOWN,
            default=d.get(CONF_TRAVEL_DOWN, DEFAULT_TRAVEL_TIME),
        ): sel.selector({"number": {"min": 1, "max": 600, "mode": "box"}}),
    }

    if include_unique:
        # unique_id is immutable; only present for the initial setup form
        schema[vol.Required(CONF_UNIQUE_ID, default=d.get(CONF_UNIQUE_ID, ""))] = sel.selector(
            {"text": {}}
        )

    return vol.Schema(schema)


def _validate_input(
    hass: HomeAssistant,
    user_input: dict[str, Any],
) -> dict[str, str]:
    """Validate fields that selectors cannot fully validate."""
    errors: dict[str, str] = {}

    if not user_input[CONF_FRIENDLY_NAME].strip():
        errors[CONF_FRIENDLY_NAME] = "required"

    try:
        Template(user_input[CONF_VALUE_TEMPLATE], hass).ensure_valid()
    except TemplateError:
        errors[CONF_VALUE_TEMPLATE] = "invalid_template"

    if not user_input[CONF_OPEN_COVER]:
        errors[CONF_OPEN_COVER] = "required"
    if not user_input[CONF_CLOSE_COVER]:
        errors[CONF_CLOSE_COVER] = "required"

    return errors


class PCCConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for PCC (one cover per entry)."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        _LOGGER.debug("PCC: async_step_user (received_input=%s)", user_input is not None)
        errors: dict[str, str] = {}

        if user_input is not None:
            unique_id = user_input[CONF_UNIQUE_ID].strip()
            errors = _validate_input(self.hass, user_input)

            if not unique_id:
                errors[CONF_UNIQUE_ID] = "required"
            else:
                legacy_duplicate = any(
                    entry.data.get(CONF_UNIQUE_ID) == unique_id
                    for entry in self._async_current_entries()
                )

                if legacy_duplicate:
                    errors[CONF_UNIQUE_ID] = "duplicate_unique_id"
                    _LOGGER.debug("PCC: duplicate legacy unique_id: %s", unique_id)
                else:
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    user_input = {
                        **user_input,
                        CONF_FRIENDLY_NAME: user_input[CONF_FRIENDLY_NAME].strip(),
                        CONF_UNIQUE_ID: unique_id,
                    }

            if not errors:
                _LOGGER.debug(
                    "PCC: creating entry title=%r unique_id=%r",
                    user_input.get(CONF_FRIENDLY_NAME),
                    user_input.get(CONF_UNIQUE_ID),
                )
                return self.async_create_entry(
                    title=user_input[CONF_FRIENDLY_NAME],
                    data=user_input,
                )

        _LOGGER.debug("PCC: showing initial setup form (includes unique_id)")
        return self.async_show_form(
            step_id="user",
            data_schema=_schema(include_unique=True),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> config_entries.OptionsFlow:
        """Expose the OptionsFlow so 'Configure' appears on the integration card."""
        _LOGGER.debug(
            "PCC: async_get_options_flow for entry_id=%s",
            config_entry.entry_id,
        )
        return PCCOptionsFlow()


class PCCOptionsFlow(config_entries.OptionsFlow):
    """Options flow for post-setup configuration (does not allow changing unique_id)."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        if user_input is not None:
            errors = _validate_input(self.hass, user_input)
            if not errors:
                user_input[CONF_FRIENDLY_NAME] = user_input[CONF_FRIENDLY_NAME].strip()
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title=user_input[CONF_FRIENDLY_NAME],
                )
                _LOGGER.debug("PCC: options saved entry_id=%s", self.config_entry.entry_id)
                return self.async_create_entry(title="", data=user_input)
        else:
            errors = {}

        defaults = (
            user_input
            if user_input is not None
            else {**self.config_entry.data, **self.config_entry.options}
        )
        _LOGGER.debug("PCC: options form opened entry_id=%s", self.config_entry.entry_id)

        schema = _schema(
            {
                **defaults,
                CONF_FRIENDLY_NAME: defaults.get(CONF_FRIENDLY_NAME, self.config_entry.title),
            },
            include_unique=False,
        )

        _LOGGER.debug(
            "PCC: showing options form (exclude unique_id) entry_id=%s",
            self.config_entry.entry_id,
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
