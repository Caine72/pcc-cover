"""Tests for the PCC Cover config and options flows."""

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_FRIENDLY_NAME, CONF_UNIQUE_ID, CONF_VALUE_TEMPLATE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pcc.const import CONF_OPEN_COVER, DOMAIN


async def test_user_flow_creates_entry(
    hass: HomeAssistant,
    entry_data: dict,
) -> None:
    """A valid form creates an entry with a normalized identity."""
    entry_data[CONF_FRIENDLY_NAME] = "  Garage door  "
    entry_data[CONF_UNIQUE_ID] = "  garage-door  "

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=entry_data,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Garage door"
    assert result["data"][CONF_UNIQUE_ID] == "garage-door"


async def test_user_flow_rejects_invalid_input(
    hass: HomeAssistant,
    entry_data: dict,
) -> None:
    """Blank identities, invalid templates, and empty actions are rejected."""
    entry_data[CONF_FRIENDLY_NAME] = " "
    entry_data[CONF_UNIQUE_ID] = " "
    entry_data[CONF_VALUE_TEMPLATE] = "{{ broken"
    entry_data[CONF_OPEN_COVER] = []

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=entry_data,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_FRIENDLY_NAME: "required",
        CONF_UNIQUE_ID: "required",
        CONF_VALUE_TEMPLATE: "invalid_template",
        CONF_OPEN_COVER: "required",
    }


async def test_user_flow_rejects_duplicate_legacy_id(
    hass: HomeAssistant,
    entry_data: dict,
) -> None:
    """Entries created before config-flow unique IDs remain protected."""
    MockConfigEntry(
        domain=DOMAIN,
        title="Existing",
        data={CONF_UNIQUE_ID: "garage-door"},
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=entry_data,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_UNIQUE_ID: "duplicate_unique_id"}


async def test_options_flow_updates_title_and_options(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    entry_data: dict,
) -> None:
    """Options update both runtime data and the integration card title."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    entry_data[CONF_FRIENDLY_NAME] = "Side gate"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={key: value for key, value in entry_data.items() if key != CONF_UNIQUE_ID},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.title == "Side gate"
    assert config_entry.options[CONF_FRIENDLY_NAME] == "Side gate"
