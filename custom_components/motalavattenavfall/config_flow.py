from __future__ import annotations

import urllib.request, json, asyncio, hashlib, requests, logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "motalavattenavfall"
_LOGGER = logging.getLogger(__name__)


DATA_SCHEMA = vol.Schema(
    {
        vol.Required("address"): str
    }
)


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input."""
    #TODO, Add validation
    address = data["address"]

    session = async_get_clientsession(hass)
    
    try:
        device_id = generate_device_id_from_address(address)
        await register_new_device(session, device_id)
        await get_plant_id_from_address(session, address,device_id)
    except Exception:
            raise InvalidAddress

    return {"title": address}


def generate_device_id_from_address(address):
    return (hashlib.md5(("7815696ecbf1c96e6894b779456d330e"+address).encode()).hexdigest()[:16])


async def register_new_device(session, device_id):
    url = "https://motala.avfallsapp.se/wp-json/nova/v1/register"
    async with session.post(url, headers={
    'Host': 'motala.avfallsapp.se',
    'x-app-token': 'undefined',
    'x-app-identifier': device_id,
    'content-type': 'application/json; charset=utf-8'
}, json={
        'identifier': device_id,
        'uuid': device_id,
        'platform': 'android',
        'version': '3.0.3.0',
        'os_version': '13',
        'model': 'HomeAssistant',
        'test': False
    }) as resp:
        data = await resp.json()
        return data


async def get_plant_id_from_address(session, address, device_id):
    """plant_id is an internal id used by the app, it is unique for every address"""
    url = "https://motala.avfallsapp.se/wp-json/nova/v1/next-pickup/search?" + (urllib.parse.urlencode({'address': address}).replace("+", "%2520"))
    async with session.get(url, headers={
    'Host': 'motala.avfallsapp.se',
    'x-app-token': 'undefined',
    'x-app-identifier': device_id,
    'content-type': 'application/json; charset=utf-8'
}) as resp:
        data = await resp.json()
        return data[(address[:1])][0]['plant_number']


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

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
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
        
class InvalidAddress(exceptions.HomeAssistantError):
    """Error to indicate the address was invalid."""