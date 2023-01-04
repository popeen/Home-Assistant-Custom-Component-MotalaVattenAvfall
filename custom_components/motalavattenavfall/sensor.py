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

CONF_TYPE = "type"
CONF_ADDRESS = "address"

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=60)

SCAN_INTERVAL = timedelta(minutes=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_TYPE): cv.string,
        vol.Required(CONF_ADDRESS): cv.string,
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None) -> None:
    """Set up the Motala Vatten & Avfall sensor platform."""

    sensor_name = config[CONF_NAME]
    sensor_type = config[CONF_TYPE]
    sensor_address = config[CONF_ADDRESS]

    add_entities([VattenAvfallSensor(sensor_name, sensor_type, sensor_address)])


class VattenAvfallSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, sensor_name, sensor_type, sensor_address):
        """Initialize the sensor."""
        
        self._name = sensor_name
        self._type = sensor_type
        self._address = sensor_address

        self._identifier = str(self.generate_device_id_from_address(self._address))

        self.register_new_device()
        plant_id = self.get_plant_id_from_address(self._address)
        self.save_address(plant_id)

        self._state = self.get_vatten_avfall_collection_date()
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
    def icon(self):
        """Icon to use in the frontend."""
        return self._icon

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self) -> None:
        """Get the latest data and updates the states."""
        self._state = self.get_vatten_avfall_collection_date()

    def generate_device_id_from_address(self, address):
        return hashlib.md5(("7815696ecbf1c96e6894b779456d330e"+address).encode()).hexdigest()[:16]

    def get_vatten_avfall_data(self):
        """This is the data we are after, it contains information about your address as well as when garbage and sludge will be collected"""
        
        if self._type == "Slam":
            return requests.get(url="https://motala.avfallsapp.se/wp-json/nova/v1/sludge-suction/list", headers={
                'Host': 'motala.avfallsapp.se',
                'x-app-identifier': self._identifier,
                'content-type': 'application/json; charset=utf-8',
                'user-agent': 'www.Home-Assistant.io - Add-On for Motala Vatten & Avfall'
            }).json()[0]['bins']
        
        else:
            return requests.get(url="https://motala.avfallsapp.se/wp-json/nova/v1/next-pickup/list", headers={
                'Host': 'motala.avfallsapp.se',
                'x-app-identifier': self._identifier,
                'content-type': 'application/json; charset=utf-8',
                'user-agent': 'www.Home-Assistant.io - Add-On for Motala Vatten & Avfall'
            }).json()[0]['bins']

    def get_plant_id_from_address(self, address):
        """plant_id is an internal id used by the app, it is unique for every address"""
        data = requests.get(url="https://motala.avfallsapp.se/wp-json/nova/v1/next-pickup/search?" + (urllib.parse.urlencode({'address': address}).replace("+", "%2520")), headers={
            'Host': 'motala.avfallsapp.se',
            'x-app-token': 'undefined',
            'x-app-identifier': self._identifier,
            'content-type': 'application/json; charset=utf-8',
            'user-agent': 'www.Home-Assistant.io - Add-On for Motala Vatten & Avfall'
        })

        return data.json()[(address[:1])][0]['plant_number']


    def register_new_device(self):
        requests.post(url='https://motala.avfallsapp.se/wp-json/nova/v1/register', headers={
            'Host': 'motala.avfallsapp.se',
            'x-app-token': 'undefined',
            'x-app-identifier': self._identifier,
            'content-type': 'application/json; charset=utf-8',
            'user-agent': 'www.Home-Assistant.io - Add-On for Motala Vatten & Avfall'
        }, json={
                'identifier': self._identifier,
                'uuid': self._identifier,
                'platform': 'android',
                'version': '3.0.3.0',
                'os_version': '13',
                'model': 'IN2023',
                'test': False
            })


    def save_address(self, plant_id):
        """Saves the given plant_id to the account. The plant_id is a unique ID based on the address.
        It can be fetched with getVattenAvfall_PlantID(identifier)"""        
        requests.post(url='https://motala.avfallsapp.se/wp-json/nova/v1/next-pickup/set-status', headers={
            'Host': 'motala.avfallsapp.se',
            'x-app-token': 'undefined',
            'x-app-identifier': self._identifier,
            'content-type': 'application/json; charset=utf-8',
            'user-agent': 'www.Home-Assistant.io - Add-On for Motala Vatten & Avfall'
        }, json={
                'plant_id': plant_id,
                'address_enabled': True,
                'notification_enabled': False,
            })

        requests.post(url='https://motala.avfallsapp.se/wp-json/nova/v1/sludge-suction/set-status', headers={
            'Host': 'motala.avfallsapp.se',
            'x-app-token': 'undefined',
            'x-app-identifier': self._identifier,
            'content-type': 'application/json; charset=utf-8',
            'user-agent': 'www.Home-Assistant.io - Add-On for Motala Vatten & Avfall'
        }, json={
                'plant_id': plant_id,
                'address_enabled': True,
                'notification_enabled': False,
            })


    def get_vatten_avfall_collection_date(self):

        # Get data
        data = self.get_vatten_avfall_data()

        
        for item in data:
            if self._address in item['address']:
                if self._type in item['type']:
                    return item['pickup_date']
        
        return None