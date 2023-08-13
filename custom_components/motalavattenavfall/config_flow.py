from __future__ import annotations
from . import common
from typing import Any

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

import asyncio
import voluptuous as vol


DATA_SCHEMA = vol.Schema(
    {
        vol.Required(common.CONF_ADDRESS): str
    }
)


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input."""
    address = data[common.CONF_ADDRESS]

    session = async_get_clientsession(hass)
    
    try:
        device_id = common.generate_device_id_from_address(address)
        await common.register_new_device(session, device_id)
        await common.get_plant_id_from_address(session, address,device_id)
    except Exception:
            raise InvalidAddress

    return {"title": address}


class ConfigFlow(config_entries.ConfigFlow, domain=common.DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                return self.async_create_entry(title=info["title"], data=user_input)
            except InvalidAddress:
                errors["base"] = "invalid_address"
            except Exception:  # pylint: disable=broad-except
                common._LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
        
class InvalidAddress(exceptions.HomeAssistantError):
    """Error to indicate the address was invalid."""