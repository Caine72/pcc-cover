import asyncio
import logging
from typing import Any

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.components.template.template_entity import TemplateEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_FRIENDLY_NAME,
    CONF_UNIQUE_ID,
    CONF_VALUE_TEMPLATE,
    STATE_CLOSED,
    STATE_OFF,
    STATE_ON,
    STATE_OPEN,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.script import Script
from homeassistant.helpers.template import Template as HATemplate

from .const import (
    CONF_CLOSE_COVER,
    CONF_OPEN_COVER,
    CONF_STOP_COVER,
    CONF_TRAVEL_DOWN,
    CONF_TRAVEL_UP,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

_OPEN_STATES = {STATE_ON, "true"}
_CLOSED_STATES = {STATE_OFF, "false"}
_VALID_STATES = _OPEN_STATES | _CLOSED_STATES


def _merged(entry: ConfigEntry) -> dict[str, Any]:
    """Options override data; fall back to data."""
    if entry.options:
        return {**entry.data, **entry.options}
    return entry.data


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PCC cover from a config entry."""
    cfg = _merged(entry)
    entity = PCCCover(
        hass=hass,
        entry=entry,
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

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        name: str,
        unique_id: str | None,
        device_class: str | None,
        value_template: str,
        open_action: list[dict[str, Any]],
        close_action: list[dict[str, Any]],
        stop_action: list[dict[str, Any]] | None,
        travel_up: int,
        travel_down: int,
    ) -> None:
        super().__init__(hass, config={}, unique_id=unique_id)

        self._attr_name = name
        self._attr_device_class = CoverDeviceClass(device_class) if device_class else None
        self._entry = entry

        self._template = HATemplate(value_template, hass)

        self._open_script = Script(hass, open_action, name, DOMAIN)
        self._close_script = Script(hass, close_action, name, DOMAIN)
        self._stop_script = Script(hass, stop_action, name, DOMAIN) if stop_action else None

        self._state: str | None = None
        self._opening_task: asyncio.Task[None] | None = None
        self._closing_task: asyncio.Task[None] | None = None
        self._travel_time_up = int(travel_up)
        self._travel_time_down = int(travel_down)

    async def async_added_to_hass(self) -> None:
        """Start tracking the state template."""
        if self._template:
            self.add_template_attribute("_state", self._template, None, self._update_state)
        await super().async_added_to_hass()

    @callback
    def _update_state(self, result: Any) -> None:
        super()._update_state(result)
        if isinstance(result, TemplateError):
            self._state = None
            return

        state = str(result).strip().lower()
        if state not in _VALID_STATES:
            self._state = None
            _LOGGER.error(
                "Invalid state: %s (expected: %s)",
                state,
                ", ".join(sorted(_VALID_STATES)),
            )
            return

        previous_state = self._state
        self._state = STATE_OPEN if state in _OPEN_STATES else STATE_CLOSED

        if previous_state == STATE_CLOSED and self._state == STATE_OPEN:
            self._reset_opening_timer()
        elif previous_state == STATE_OPEN and self._state == STATE_CLOSED:
            self._reset_closing_timer()

    def _start_opening_timer(self) -> None:
        self._reset_closing_timer()
        self._reset_opening_timer()

        self._opening_task = self._entry.async_create_task(
            self.hass,
            self._async_timer(self._travel_time_up, "opening"),
            name="PCC opening travel timer",
        )

    def _reset_opening_timer(self) -> None:
        if self._opening_task:
            self._opening_task.cancel()
            self._opening_task = None

    def _start_closing_timer(self) -> None:
        self._reset_opening_timer()
        self._reset_closing_timer()

        self._closing_task = self._entry.async_create_task(
            self.hass,
            self._async_timer(self._travel_time_down, "closing"),
            name="PCC closing travel timer",
        )

    def _reset_closing_timer(self) -> None:
        if self._closing_task:
            self._closing_task.cancel()
            self._closing_task = None

    async def _async_timer(self, delay: int, direction: str) -> None:
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return

        if direction == "opening":
            self._opening_task = None
        else:
            self._closing_task = None
        self.async_write_ha_state()

    @property
    def is_closed(self) -> bool | None:
        if self._state is None:
            return None
        return self._state == STATE_CLOSED

    @property
    def is_opening(self) -> bool:
        return self._opening_task is not None

    @property
    def is_closing(self) -> bool:
        return self._closing_task is not None

    @property
    def supported_features(self) -> CoverEntityFeature:
        features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
        if self._stop_script:
            features |= CoverEntityFeature.STOP
        return features

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover and start simulated travel."""
        self._start_opening_timer()
        self.async_write_ha_state()
        try:
            await self._open_script.async_run(context=self._context)
        except Exception:
            self._reset_opening_timer()
            self.async_write_ha_state()
            raise

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover and start simulated travel."""
        self._start_closing_timer()
        self.async_write_ha_state()
        try:
            await self._close_script.async_run(context=self._context)
        except Exception:
            self._reset_closing_timer()
            self.async_write_ha_state()
            raise

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover and clear simulated travel."""
        if self._stop_script:
            self._reset_opening_timer()
            self._reset_closing_timer()
            self.async_schedule_update_ha_state()
            await self._stop_script.async_run(context=self._context)

    async def async_will_remove_from_hass(self) -> None:
        """Cancel travel timers before the entity is removed."""
        self._reset_opening_timer()
        self._reset_closing_timer()
        await super().async_will_remove_from_hass()
