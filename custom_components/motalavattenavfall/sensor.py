"""Platform for sensor integration."""
import urllib.request, json, asyncio, hashlib, requests
from datetime import timedelta
from urllib import request

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

DOMAIN = "motalavattenavfall"

CONF_ADDRESS = "address"

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=60)

SCAN_INTERVAL = timedelta(minutes=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADDRESS): cv.string
    }
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    session = async_get_clientsession(hass)
    address = hass.data[DOMAIN][config_entry.entry_id]
    
    #Register HA as a device and save the address to the account
    #TODO, This should only be done the first time
    device_id = generate_device_id_from_address(address)
    plant_id = await get_plant_id_from_address(session, address, device_id)
    await save_address(session, plant_id, device_id)
    data = await get_vatten_avfall_data(session, device_id)

    entities = []

    for sensor in data:
        entities.append(VattenAvfallSensor(sensor['type'], sensor['address'], sensor['service_id'], device_id))

    async_add_entities(entities, update_before_add=True)


def generate_device_id_from_address(address):
    return (hashlib.md5(("7815696ecbf1c96e6894b779456d330e"+address).encode()).hexdigest()[:16])


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


async def save_address(session, plant_id, device_id):
    """Saves the given plant_id to the account. The plant_id is a unique ID based on the address.
    It can be fetched with getVattenAvfall_PlantID(identifier)"""
    url = "https://motala.avfallsapp.se/wp-json/nova/v1/next-pickup/set-status"
    await session.post(url, headers={
        'Host': 'motala.avfallsapp.se',
        'x-app-token': 'undefined',
        'x-app-identifier': device_id,
        'content-type': 'application/json; charset=utf-8'
    }, json={
            'plant_id': plant_id,
            'address_enabled': True,
            'notification_enabled': False,
    })
    url = "https://motala.avfallsapp.se/wp-json/nova/v1/sludge-suction/set-status"
    await session.post(url, headers={
        'Host': 'motala.avfallsapp.se',
        'x-app-token': 'undefined',
        'x-app-identifier': device_id,
        'content-type': 'application/json; charset=utf-8'
    }, json={
            'plant_id': plant_id,
            'address_enabled': True,
            'notification_enabled': False,
    })


async def get_vatten_avfall_data(session, device_id):
    """This is the data we are after, it contains information about your address as well as when garbage and sludge will be collected"""
    pickup = []
    url = "https://motala.avfallsapp.se/wp-json/nova/v1/next-pickup/list"
    async with session.get(url, headers={
        'Host': 'motala.avfallsapp.se',
        'x-app-token': 'undefined',
        'x-app-identifier': device_id,
        'content-type': 'application/json; charset=utf-8'
    }) as resp:
        data = await resp.json()
        if len(data) > 0:
            pickup += data[0]['bins']
    url = "https://motala.avfallsapp.se/wp-json/nova/v1/sludge-suction/list"
    async with session.get(url, headers={
        'Host': 'motala.avfallsapp.se',
        'x-app-token': 'undefined',
        'x-app-identifier': device_id,
        'content-type': 'application/json; charset=utf-8'
    }) as resp:
        data = await resp.json()
        if len(data) > 0:
            pickup += data[0]['bins']

    return pickup


class VattenAvfallSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, sensor_type, sensor_address, identifier, device_id):
        """Initialize the sensor."""

        self._attr_unique_id = identifier
        self._device_id = device_id
        self._name = sensor_address + " " + sensor_type
        self._type = sensor_type
        self._address = sensor_address
        self._state = None
        self._extra = {}

        if self._type == "Slam":
            self._icon = "mdi:water"
        else:
            self._icon = "mdi:delete"
        
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
    
    @property
    def extra_state_attributes(self):
        #Make sure it has been set
        attributes = self._extra
        if hasattr(self, "add_state_attributes"):
            attributes = {**attributes, **self.add_state_attributes}
        return attributes
    
    @property
    def icon(self):
        """Icon to use in the frontend."""
        return self._icon

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self) -> None:
        """Get the latest data and updates the states."""
        session = async_get_clientsession(self.hass)
        # Get data
        data = await get_vatten_avfall_data(session, self._device_id)
        for item in data:
            if self._attr_unique_id == item['service_id']:
                self._state = item['pickup_date']
                self._extra = item
        return None