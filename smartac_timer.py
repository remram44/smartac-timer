import aiohttp
import asyncio
from datetime import datetime, timedelta
import json
import logging
import os
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles


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


# Device timers
timers = {}


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
        if os.path.exists('cookies.bin'):
            logger.info("Loading cookies from file")
            get_http_client._instance.cookie_jar.load('cookies.bin')
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
        http_client.cookie_jar.save('cookies.bin')


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
        if device_id in timers:
            mode, time, _ = timers[device_id]
            device_info['timer'] = dict(
                when=time.isoformat() + 'Z',
                mode=mode,
            )
        devices.append(device_info)

    return JSONResponse(dict(
        devices=devices,
    ))


async def do_switch(device, mode):
    try:
        set_mode = dict(on='SwitchOn', off='SwitchOff')[mode]
    except KeyError:
        raise HTTPException(404)

    # Cancel pending timers
    if device in timers:
        _, _, fut = timers.pop(device)
        fut.cancel()

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


async def switch(request):
    device = request.path_params['device']
    mode = request.path_params['mode']
    if mode not in ('on', 'off'):
        raise HTTPException(400)

    await do_switch(device, mode)

    return JSONResponse({})


async def sleep_then_switch(delay, device, mode):
    try:
        await asyncio.sleep(delay)
        timers.pop(device, None)
        await asyncio.shield(do_switch(device, mode))
    except asyncio.CancelledError:
        pass


async def set_timer(request):
    device = request.path_params['device']
    obj = await request.json()
    delay = obj.pop('delay')
    mode = obj.pop('mode', 'off')
    if mode not in ('on', 'off'):
        raise HTTPException(400)
    if obj:
        raise HTTPException(400)

    if device in timers:
        _, _, fut = timers.pop(device)
        fut.cancel()

    fut = asyncio.get_event_loop().create_task(
        sleep_then_switch(delay, device, mode),
    )
    timers[device] = mode, datetime.utcnow() + timedelta(seconds=delay), fut

    return JSONResponse({})


routes = [
    Route('/api/status', status),
    Route(
        '/api/switch/{device:int}/{mode}', switch,
        methods=['POST'],
    ),
    Route(
        '/api/set-timer/{device:int}', set_timer,
        methods=['POST'],
    ),
    Mount('/', app=StaticFiles(directory='static', html=True)),
]


app = Starlette(routes=routes, debug=True)
