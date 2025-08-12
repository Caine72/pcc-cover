from __future__ import annotations
import asyncio
import logging
from homeassistant.components.cover import (
    ENTITY_ID_FORMAT,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_FRIENDLY_NAME,
    CONF_UNIQUE_ID,
    CONF_VALUE_TEMPLATE,
    STATE_CLOSED,
    STATE_OPEN,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import callback
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.script import Script
from homeassistant.helpers.template import Template as HATemplate
from homeassistant.components.template.template_entity import TemplateEntity
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)
_VALID_STATES = [STATE_ON, STATE_OFF, "true", "false"]

CONF_OPEN_COVER = "open_cover"
CONF_CLOSE_COVER = "close_cover"
CONF_STOP_COVER = "stop_cover"
CONF_TRAVEL_UP = "travelling_time_up"
CONF_TRAVEL_DOWN = "travelling_time_down"


def _merged(entry):
    """Options override data; fall back to data."""
    if entry.options:
        return {**entry.data, **entry.options}
    return entry.data


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up PCC cover from a config entry."""
    cfg = _merged(entry)
    entity = PCCCover(
        hass=hass,
        name=cfg[CONF_FRIENDLY_NAME],
        unique_id=cfg.get(CONF_UNIQUE_ID, entry.unique_id),
        device_class=cfg.get(CONF_DEVICE_CLASS),
        value_template=cfg[CONF_VALUE_TEMPLATE],
        open_action=cfg[CONF_OPEN_COVER],
        close_action=cfg[CONF_CLOSE_COVER],
        stop_action=cfg.get(CONF_STOP_COVER),
        travel_up=int(cfg[CONF_TRAVEL_UP]),
        travel_down=int(cfg[CONF_TRAVEL_DOWN]),
    )
    async_add_entities([entity])


class PCCCover(TemplateEntity, CoverEntity):
    """PCC Template-based cover with simulated opening/closing."""

    def __init__(self, hass, name, unique_id, device_class, value_template,
                 open_action, close_action, stop_action,
                 travel_up, travel_down):
        super().__init__(hass, config={}, unique_id=unique_id)

        self._attr_name = name

        self.entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, name, hass=hass)

        self._device_class = device_class

        self._template = HATemplate(value_template, hass)

        self._open_script = Script(hass, open_action, name, DOMAIN)
        self._close_script = Script(hass, close_action, name, DOMAIN)
        self._stop_script = Script(hass, stop_action, name, DOMAIN) if stop_action else None

        self._state = None
        self._opening_task = None
        self._closing_task = None
        self._travel_time_up = int(travel_up)
        self._travel_time_down = int(travel_down)

    async def async_added_to_hass(self):
        if self._template:
            self.add_template_attribute("_state", self._template, None, self._update_state)
        await super().async_added_to_hass()

    @callback
    def _update_state(self, result):
        super()._update_state(result)
        if isinstance(result, TemplateError):
            self._state = None
            return

        state = str(result).lower()
        if state not in _VALID_STATES:
            self._state = None
            _LOGGER.error("Invalid state: %s (expected: %s)", state, ", ".join(_VALID_STATES))
            return

        if self._state == STATE_CLOSED and state in ("true", STATE_ON):
            self._start_opening_timer()
            self._state = STATE_OPEN
        elif self._state == STATE_OPEN and state in ("false", STATE_OFF):
            self._state = STATE_CLOSED
            self._reset_closing_timer()
        else:
            self._state = STATE_OPEN if state in ("true", STATE_ON) else STATE_CLOSED

    def _start_opening_timer(self):
        self._reset_opening_timer()
        async def _done():
            self._opening_task = None
            self.async_schedule_update_ha_state()
        self._opening_task = asyncio.create_task(self._async_timer(self._travel_time_up, _done))

    def _reset_opening_timer(self):
        if self._opening_task:
            self._opening_task.cancel()
            self._opening_task = None

    def _start_closing_timer(self):
        self._reset_closing_timer()
        async def _done():
            self._closing_task = None
            self.async_schedule_update_ha_state()
        self._closing_task = asyncio.create_task(self._async_timer(self._travel_time_down, _done))

    def _reset_closing_timer(self):
        if self._closing_task:
            self._closing_task.cancel()
            self._closing_task = None

    async def _async_timer(self, delay, callback):
        try:
            await asyncio.sleep(delay)
            await callback()
        except asyncio.CancelledError:
            pass

    @property
    def device_class(self):
        return self._device_class

    @property
    def is_closed(self):
        return self._state == STATE_CLOSED

    @property
    def is_opening(self):
        return self._opening_task is not None

    @property
    def is_closing(self):
        return self._closing_task is not None

    @property
    def supported_features(self):
        features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
        if self._stop_script:
            features |= CoverEntityFeature.STOP
        return features

    async def async_open_cover(self, **kwargs):
        if self._open_script:
            await self._open_script.async_run(context=self._context)

    async def async_close_cover(self, **kwargs):
        if self._close_script:
            self._start_closing_timer()
            self.async_schedule_update_ha_state()
            await self._close_script.async_run(context=self._context)

    async def async_stop_cover(self, **kwargs):
        if self._stop_script:
            await self._stop_script.async_run(context=self._context)

