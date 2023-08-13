import urllib.request, hashlib, logging

DOMAIN = "motalavattenavfall"

CONF_ADDRESS = "address"
_LOGGER = logging.getLogger(__name__)

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