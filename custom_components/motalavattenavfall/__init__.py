from __future__ import annotations
from . import common

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

PLATFORMS: list[str] = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(common.DOMAIN, {})[entry.entry_id] = entry.data[common.CONF_ADDRESS]
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


