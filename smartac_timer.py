import aiohttp
import json
import logging
import os
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.routing import Route


logger = logging.getLogger('smartac_timer')
f = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
h = logging.StreamHandler()
h.setFormatter(f)
logger.setLevel(logging.INFO)
logger.addHandler(h)


# Load settings
with open(os.path.join(os.path.dirname(__file__),
                       'settings.py'), 'rb') as fp:
    SETTINGS = {}
    exec(fp.read(), SETTINGS, SETTINGS)


def get_http_client():
    if get_http_client._instance is None:
        get_http_client._instance = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/74.0.3729.169 '
                              'Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': '*/*',
            },
        )
    return get_http_client._instance


get_http_client._instance = None


async def mymodlet_req(method, path, **kwargs):
    http_client = get_http_client()
    re_authenticated = False

    while True:
        async with http_client.request(
            method,
            'https://web.mymodlet.com' + path,
            **kwargs,
        ) as response:
            if response.status == 401 and not re_authenticated:
                # Try and re-authenticate
                pass
            else:
                response.raise_for_status()
                return response

        # Re-authenticate
        logger.warning("Re-authenticating")
        # Get fresh cookies
        http_client.cookie_jar.clear()
        async with http_client.get(
            'https://web.mymodlet.com/'
            + 'Account/Login/?ReturnUrl=%2F&ReturnUrl=%2F',
            allow_redirects=True,
        ) as response:
            response.raise_for_status()
        # Post login/password to start new session
        async with http_client.post(
            'https://web.mymodlet.com/Account/Login?returnUrl=/',
            allow_redirects=False,
            json={
                'data': json.dumps({
                    'Email': SETTINGS['email'],
                    'Password': SETTINGS['password'],
                }),
            },
        ):
            response.raise_for_status()
            re_authenticated = True


mymodlet_get = lambda url, **kwargs: mymodlet_req('GET', url, **kwargs)
mymodlet_post = lambda url, **kwargs: mymodlet_req('POST', url, **kwargs)


def temp_f(f):
    return dict(
        farenheit=f,
        celsius=round((f-32) * 5 / 9),
    )


async def status(request):
    response = await mymodlet_get('/Devices/UpdateData')

    status = await response.text()

    # It's a JSON string with JSON inside (double encoded)
    status = json.loads(status)
    assert isinstance(status, str)
    status = json.loads(status)

    modlets = {}
    for modlet in status['SmartACs']:
        for channel in modlet['modlet']['modletChannels']:
            modlets[channel['deviceId']] = modlet
    devices = []
    for device in status['Devices']:
        device_id = device['deviceId']
        if device['type'].lower() == 'air conditioner':
            kind = 'ac'
        else:
            kind = None
        device_info = dict(
            kind=kind,
            id=device_id,
            name=device['deviceName'],
            status='on' if device['isOn'] else 'off',
        )
        if device_id in modlets:
            modlet = modlets[device_id]
            if 'thermostat' in modlet:
                device_info['thermostat'] = temp_f(
                    modlet['thermostat']['targetTemperature'],
                )
                device_info['temperature'] = temp_f(
                    modlet['thermostat']['currentTemperature'],
                )
        devices.append(device_info)

    return JSONResponse(dict(
        devices=devices,
    ))


async def switch(request):
    mode = request.path_params['mode']
    device = request.path_params['device']

    try:
        set_mode = dict(on='SwitchOn', off='SwitchOff')[mode]
    except KeyError:
        raise HTTPException(404)

    logger.info("Switching AC %s", mode)
    response = await mymodlet_post(
        '/Devices/%s' % set_mode,
        headers={
            'Referer': 'https://web.mymodlet.com/Devices',
            'Content-Type': 'application/json',
        },
        json={
            'data': '{"id":"%s"}' % device,  # Yes, it is double-json-encoded
        },
    )
    response.raise_for_status()
    return JSONResponse({})


routes = [
    Route('/api/status', status),
    Route(
        '/api/switch/{device:int}/{mode}', switch,
        methods=['POST'],
    ),
]


app = Starlette(routes=routes, debug=True)
