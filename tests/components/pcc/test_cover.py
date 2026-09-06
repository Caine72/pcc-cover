"""Tests for PCC Cover entity behavior."""

from homeassistant.components.cover import DOMAIN as COVER_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_STOP_COVER,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

ENTITY_ID = "cover.garage_door"


async def _load_entry(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    hass.states.async_set("binary_sensor.garage_door", "off")
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == STATE_CLOSED


async def test_commands_manage_mutually_exclusive_travel(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Commands start, reverse, and stop simulated travel consistently."""
    await _load_entry(hass, config_entry)

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    assert hass.states.get(ENTITY_ID).state == STATE_OPENING

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    assert hass.states.get(ENTITY_ID).state == STATE_CLOSING

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    assert hass.states.get(ENTITY_ID).state == STATE_CLOSED


async def test_template_endpoint_ends_matching_travel(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """A changed end-position template ends simulated movement early."""
    await _load_entry(hass, config_entry)

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    hass.states.async_set("binary_sensor.garage_door", "on")
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY_ID).state == STATE_OPEN


async def test_invalid_template_result_is_unknown(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """An unsupported template result must not be reported as open."""
    hass.config_entries.async_update_entry(
        config_entry,
        data={
            **config_entry.data,
            "value_template": "invalid",
        },
    )

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY_ID).state == STATE_UNKNOWN


async def test_unload_cancels_travel_and_removes_entity(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Config entry unload cleans up an active timer and entity."""
    await _load_entry(hass, config_entry)
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE
