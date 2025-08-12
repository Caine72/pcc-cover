from __future__ import annotations
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

_LOGGER = logging.getLogger(__name__)

DOMAIN = "pcc"
PLATFORMS: list[Platform] = [Platform.COVER]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Legacy setup (not used)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PCC from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload entity when options change
    async def _update_listener(hass: HomeAssistant, updated_entry: ConfigEntry) -> None:
        await hass.config_entries.async_reload(updated_entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload PCC config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

