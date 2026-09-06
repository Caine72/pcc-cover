"""Fixtures for PCC Cover tests."""

import pytest
from homeassistant.const import CONF_FRIENDLY_NAME, CONF_UNIQUE_ID, CONF_VALUE_TEMPLATE
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pcc.const import (
    CONF_CLOSE_COVER,
    CONF_OPEN_COVER,
    CONF_STOP_COVER,
    CONF_TRAVEL_DOWN,
    CONF_TRAVEL_UP,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations in every test."""


@pytest.fixture
def entry_data() -> dict:
    """Return a valid PCC config entry payload."""
    return {
        CONF_FRIENDLY_NAME: "Garage door",
        CONF_UNIQUE_ID: "garage-door",
        CONF_VALUE_TEMPLATE: "{{ is_state('binary_sensor.garage_door', 'on') }}",
        CONF_OPEN_COVER: [{"delay": 0}],
        CONF_CLOSE_COVER: [{"delay": 0}],
        CONF_STOP_COVER: [{"delay": 0}],
        CONF_TRAVEL_UP: 600,
        CONF_TRAVEL_DOWN: 600,
    }


@pytest.fixture
def config_entry(hass: HomeAssistant, entry_data: dict) -> MockConfigEntry:
    """Create a PCC config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Garage door",
        data=entry_data,
        unique_id="garage-door",
    )
    entry.add_to_hass(hass)
    return entry
