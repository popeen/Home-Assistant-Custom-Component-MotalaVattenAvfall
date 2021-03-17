"""Platform for sensor integration."""
import urllib.request, json, asyncio, hashlib
from datetime import timedelta

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

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Motala Vatten & Avfall sensor platform."""

    sensor_name = config[CONF_NAME]
    sensor_type = config[CONF_TYPE]
    sensor_address = config[CONF_ADDRESS]

    async_add_entities([VattenAvfallSensor(sensor_name, sensor_type, sensor_address)])


class VattenAvfallSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, sensor_name, sensor_type, sensor_address):
        """Initialize the sensor."""
        self._name = sensor_name
        self._type = sensor_type
        self._address = sensor_address
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
    async def async_update(self):
        """Get the latest data and updates the states."""
        try:
            self._state = self.get_vatten_avfall_collection_date()
        except (asyncio.TimeoutError, aiohttp.ClientError, ValueError) as error:
            _LOGGER.error("Could not fetch data: %s", error)

    def generate_device_id_from_address(self, address):
        return "hass" + hashlib.md5(address.encode()).hexdigest()[:12]

    def get_vatten_avfall_data(self, identifier):
        """This is the data we are after, it contains information about your address as well as when garbage and sludge will be collected"""
        req = urllib.request.Request(
            "https://motala.avfallsappen.se/wp-json/app/v1/next-pickup",
            data=None,
            headers={
                'pragma': 'no-cache',
                'User-Agent': 'www.Home-Assistant.io - Add-On for Motala Vatten & Avfall',
                'Accept': 'application/json, text/plain, */*',
                'cache-control': 'no-cache',
                'x-app-language': 'sv',
                'x-app-identifier': identifier,
                'x-requested-with': 'se.motala.avfallsapp',
                'sec-fetch-site': 'cross-site',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'accept-encoding': 'deflate',
                'accept-language': 'en-US,en;q=0.9,sv-SE;q=0.8,sv;q=0.7',
            }
        )
        with urllib.request.urlopen(req) as url:
            data = json.loads(url.read().decode())
        return data

    def get_plant_id_from_address(self, identifier, address):
        """plant_id is an internal id used by the app, it is unique for every address"""
        req = urllib.request.Request(
            "https://motala.avfallsappen.se/wp-json/app/v1/address-flat?" + urllib.parse.urlencode({'address': address}),
            data=None,
            headers={
                'Host': 'motala.avfallsappen.se',
                'pragma': 'no-cache',
                'Accept': 'application/json, text/plain, */*',
                'cache-control': 'no-cache',
                'x-app-language': 'sv',
                'x-app-identifier': identifier,
                'User-Agent': 'www.Home-Assistant.io - Add-On for Motala Vatten & Avfall',
                'x-requested-with': 'se.motala.avfallsapp',
                'sec-fetch-site': 'cross-site',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'accept-encoding': 'deflate',
                'accept-language': 'en-US,en;q=0.9,sv-SE;q=0.8,sv;q=0.7',
            }
        )


        with urllib.request.urlopen(req) as url:
            data = json.loads(url.read().decode())
        return data[1]['plant_number']


    def register_new_device(self, identifier):
        req = urllib.request.Request(
            "https://motala.avfallsappen.se/wp-json/app/v1/register",
            data= json.dumps({
                'identifier': identifier,
                'platform': 'android',
                'test_token': 0
            }).encode("utf8"),
            headers={
                'Host': 'motala.avfallsappen.se',
                'pragma': 'no-cache',
                'Accept': 'application/json, text/plain, */*',
                'cache-control': 'no-cache',
                'x-app-language': 'sv',
                'x-app-identifier': identifier,
                'x-app-version': '1.4.1',
                'User-Agent': 'www.Home-Assistant.io - Add-On for Motala Vatten & Avfall',
                'x-requested-with': 'se.motala.avfallsapp',
                'sec-fetch-site': 'cross-site',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'accept-encoding': 'deflate',
                'accept-language': 'en-US,en;q=0.9,sv-SE;q=0.8,sv;q=0.7',
                'content-type': 'application/json;charset=UTF-8'
            },
            method='POST'
        )
        with urllib.request.urlopen(req) as url:
            data = json.loads(url.read().decode())
        return data


    def save_address(self, identifier, plant_id):
        """Saves the given plant_id to the account. The plant_id is a unique ID based on the address.
        It can be fetched with getVattenAvfall_PlantID(identifier)"""
        req = urllib.request.Request(
            "https://motala.avfallsappen.se/wp-json/app/v1/save-address",
            data= json.dumps({
                'plant_id': plant_id,
                'notification_enabled': True,
            }).encode("utf8"),
            headers={
                'Host': 'motala.avfallsappen.se',
                'pragma': 'no-cache',
                'Accept': 'application/json, text/plain, */*',
                'cache-control': 'no-cache',
                'x-app-language': 'sv',
                'x-app-identifier': identifier,
                'User-Agent': 'www.Home-Assistant.io - Add-On for Motala Vatten & Avfall',
                'x-requested-with': 'se.motala.avfallsapp',
                'sec-fetch-site': 'cross-site',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'accept-encoding': 'deflate',
                'accept-language': 'en-US,en;q=0.9,sv-SE;q=0.8,sv;q=0.7',
                'content-type': 'application/json;charset=UTF-8'
            },
            method='POST'
        )
        urllib.request.urlopen(req)
        req = urllib.request.Request(
            "https://motala.avfallsappen.se/wp-json/app/v1/save-address-sludge",
            data=json.dumps({
                'plant_id': plant_id,
                'notification_enabled': True,
            }).encode("utf8"),
            headers={
                'Host': 'motala.avfallsappen.se',
                'pragma': 'no-cache',
                'Accept': 'application/json, text/plain, */*',
                'cache-control': 'no-cache',
                'x-app-language': 'sv',
                'x-app-identifier': identifier,
                'User-Agent': 'www.Home-Assistant.io - Add-On for Motala Vatten & Avfall',
                'x-requested-with': 'se.motala.avfallsapp',
                'sec-fetch-site': 'cross-site',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'accept-encoding': 'deflate',
                'accept-language': 'en-US,en;q=0.9,sv-SE;q=0.8,sv;q=0.7',
                'content-type': 'application/json;charset=UTF-8'
            },
            method='POST'
        )
        urllib.request.urlopen(req)

    def is_address_saved(self, data, address):
        """Check if the specified address is in the data."""
        isSaved = False
        try:
            for item in data:
                if address in item['address']:
                    isSaved = True
                    break
        except:
            #This happens on newly registered accounts where no address exist, just ignore it as isSaved is already set to False
            pass
        return isSaved


    def get_vatten_avfall_collection_date(self):
        identifier = self.generate_device_id_from_address(self._address)

        # Get data
        data = self.get_vatten_avfall_data(identifier)

        # if the address is not in data, add it to the account and get data again. Since we always add it the first time we assume we also need to register the account
        if not self.is_address_saved(data, self._address):
            self.register_new_device(identifier)
            plant_id = self.get_plant_id_from_address(identifier, self._address)
            self.save_address(identifier, plant_id)
            data = self.get_vatten_avfall_data(identifier)

        for data2 in data:
            if self._address in data2['address']:
                for data3 in data2['types']:
                    if self._type in data3['type']:
                        return data3['pickup_date']
                        break
                break
        return None