"""Support for covers which integrate with other components."""
import logging

import voluptuous as vol

from homeassistant.components.cover import (
    DEVICE_CLASSES_SCHEMA,
    ENTITY_ID_FORMAT,
    PLATFORM_SCHEMA,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ENTITY_PICTURE_TEMPLATE,
    CONF_FRIENDLY_NAME,
    CONF_ICON_TEMPLATE,
    CONF_UNIQUE_ID,
    CONF_VALUE_TEMPLATE,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
    STATE_OFF,
    STATE_ON
)
from homeassistant.core import callback
from homeassistant.exceptions import TemplateError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.script import Script

from homeassistant.components.template.const import CONF_AVAILABILITY_TEMPLATE, DOMAIN, PLATFORMS
from homeassistant.components.template.template_entity import (
    TEMPLATE_ENTITY_COMMON_SCHEMA_LEGACY,
    TemplateEntity,
    rewrite_common_legacy_to_modern_conf,
)
from threading import Timer

_LOGGER = logging.getLogger(__name__)
_VALID_STATES = [
    STATE_ON,
    STATE_OFF,
    "true",
    "false",
]

CONF_COVERS = "covers"

OPEN_ACTION = "open_cover"
CLOSE_ACTION = "close_cover"
STOP_ACTION = "stop_cover"

CONF_TRAVELLING_TIME_DOWN = 'travelling_time_down'
CONF_TRAVELLING_TIME_UP = 'travelling_time_up'
DEFAULT_TRAVEL_TIME = 25


COVER_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(OPEN_ACTION): cv.SCRIPT_SCHEMA,
            vol.Required(CLOSE_ACTION): cv.SCRIPT_SCHEMA,
            vol.Optional(STOP_ACTION): cv.SCRIPT_SCHEMA,
            vol.Required(CONF_VALUE_TEMPLATE): cv.template,
            vol.Optional(CONF_AVAILABILITY_TEMPLATE): cv.template,
            vol.Optional(CONF_ICON_TEMPLATE): cv.template,
            vol.Optional(CONF_ENTITY_PICTURE_TEMPLATE): cv.template,
            vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
            vol.Optional(CONF_FRIENDLY_NAME): cv.string,
            vol.Optional(CONF_UNIQUE_ID): cv.string,
            vol.Optional(CONF_TRAVELLING_TIME_DOWN, default=DEFAULT_TRAVEL_TIME): cv.positive_int,
            vol.Optional(CONF_TRAVELLING_TIME_UP, default=DEFAULT_TRAVEL_TIME): cv.positive_int,
        }
    ),
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_COVERS): cv.schema_with_slug_keys(COVER_SCHEMA)}
)


async def _async_create_entities(hass, config):
    """Create the Template cover."""
    covers = []

    for object_id, entity_config in config[CONF_COVERS].items():
        entity_config = rewrite_common_legacy_to_modern_conf(hass,entity_config)

        unique_id = entity_config.get(CONF_UNIQUE_ID)

        covers.append(
            PCCCover(
                hass,
                object_id,
                entity_config,
                unique_id,
            )
        )

    return covers



async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Template cover."""

    await async_setup_reload_service(hass, DOMAIN, PLATFORMS)
    async_add_entities(await _async_create_entities(hass, config))


class PCCCover(TemplateEntity, CoverEntity):
    """Representation of a Template cover."""

    def __init__(
        self,
        hass,
        object_id,
        config,
        unique_id,
    ):
        """Initialize the Template cover."""
        super().__init__(
            hass, config=config, fallback_name=object_id, unique_id=unique_id
        )
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, object_id, hass=hass
        )
        friendly_name = config.get(CONF_FRIENDLY_NAME, object_id)
        open_action = config.get(OPEN_ACTION)
        close_action = config.get(CLOSE_ACTION)
        stop_action = config.get(STOP_ACTION)

        self._name = friendly_name
        self._template = config.get(CONF_VALUE_TEMPLATE)
        self._device_class = config.get(CONF_DEVICE_CLASS)
        self._open_script = None

        domain = __name__.split(".")[-2]
        if open_action is not None:
            self._open_script = Script(hass, open_action, friendly_name, domain)
        self._close_script = None
        if close_action is not None:
            self._close_script = Script(hass, close_action, friendly_name, domain)
        self._stop_script = None
        if stop_action is not None:
            self._stop_script = Script(hass, stop_action, friendly_name, domain)
        self._state = None
        self._unique_id = unique_id
        self._opening_timer = None
        self._closing_timer = None
        self._travel_time_down = config.get(CONF_TRAVELLING_TIME_DOWN)
        self._travel_time_up = config.get(CONF_TRAVELLING_TIME_UP)

    async def async_added_to_hass(self):
        """Register callbacks."""

        if self._template:
            self.add_template_attribute(
                "_state", self._template, None, self._update_state
            )
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
            _LOGGER.error(
                "Received invalid cover is_on state: %s. Expected: %s",
                state,
                ", ".join(_VALID_STATES)
            )
            return
        
        if self._state == STATE_CLOSED:         # cover is closed
            if state in ("true", STATE_ON):     # closed -> open
                self._startOpeningTimer()
                self._state = STATE_OPEN
        elif self._state == STATE_OPEN:         # cover is open
            if state in ("false", STATE_OFF):   # open -> closed
                self._state = STATE_CLOSED
                self._resetClosingTimer()
        else:                                   # we don't know the cover state
            if state in ("true", STATE_ON):     
                self._state = STATE_OPEN        # cover is open
            else:
                self._state = STATE_CLOSED      # cover is closed
        
    def _startOpeningTimer(self):
        self._resetOpeningTimer()
        def _timer_done():
            self._opening_timer = None
            self.hass.loop.call_soon_threadsafe(self.async_schedule_update_ha_state)
        
        self._opening_timer = Timer(self._travel_time_up, _timer_done)
        self._opening_timer.start()

    def _resetOpeningTimer(self):
        if self._opening_timer:
            self._opening_timer.cancel()
            self._opening_timer = None        

    def _startClosingTimer(self):
        self._resetClosingTimer()
        def _timer_done():
            self._closing_timer = None
            self.hass.loop.call_soon_threadsafe(self.async_schedule_update_ha_state)
        
        self._closing_timer = Timer(self._travel_time_down, _timer_done)
        self._closing_timer.start()

    def _resetClosingTimer(self):
        if self._closing_timer:
            self._closing_timer.cancel()
            self._closing_timer = None
    

    @property
    def name(self):
        """Return the name of the cover."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique id of this cover."""
        return self._unique_id

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return self._state == STATE_CLOSED

    @property
    def is_opening(self):
        """Return if the cover is opening."""
        return self._opening_timer is not None
    
    @property
    def is_closing(self):
        """Return if the cover is closing."""
        return self._closing_timer is not None


    @property
    def device_class(self):
        """Return the device class of the cover."""
        return self._device_class

    @property
    def supported_features(self):
        """Flag supported features."""
        supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

        if self._stop_script is not None:
            supported_features |= CoverEntityFeature.STOP

        return supported_features

    async def async_open_cover(self, **kwargs):
        """Move the cover up."""
        if self._open_script:
            await self._open_script.async_run(context=self._context)

    async def async_close_cover(self, **kwargs):
        """Move the cover down."""
        if self._close_script:
            self._startClosingTimer()
            self.async_schedule_update_ha_state()
            await self._close_script.async_run(context=self._context)

    async def async_stop_cover(self, **kwargs):
        """Fire the stop action."""
        if self._stop_script:
            await self._stop_script.async_run(context=self._context)
