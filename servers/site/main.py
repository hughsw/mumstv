from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import httpx
import xmltodict

app = FastAPI()


app.mount('/static', StaticFiles(directory='static'), name='static')

templates = Jinja2Templates(directory='templates')


@app.get('/', response_class=HTMLResponse)
async def read_root(request: Request):

    response = templates.TemplateResponse(
        request=request, name='index.html', context=dict(
            site = 'b827eb7c4a78',
            device = '78669dcceb63',
        )
    )
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.get('/items/{item_id}')
async def read_item(item_id: int, q: str | None = None):
    return {'item_id': item_id, 'q': q}

mac_filename = '/sys/class/net/wlan0/address'
with open(mac_filename, 'rt') as mac_file:
    site_id = ''.join(mac_file.read().strip().split(':'))

print(f'site_id: {site_id}')

site_prefix = f'/api/{site_id}'
# query/device-info

#get_site = f'/api/{site_id}/{{device_id}}/{{item_id}}'
#print(f'get_site: {get_site}')
@app.get(site_prefix + '/device/{device_id}/{item_id}')
async def read_site_item(device_id: str, item_id: int, q: str | None = None):
    return {
        'site_id': site_id,
        'device_id': device_id,
        'item_id': item_id,
        'q': q,
    }

devices = (
    {'cache-control': 'max-age=3600',
     'device-group.roku.com': 'E3E7288623F19FA4030E',
     'ext': '',
     'location': 'http://192.168.58.103:8060/',
     'server': 'Roku/15.1.4 UPnP/1.0 Roku/15.1.4',
     'st': 'roku:ecp',
     'usn': 'uuid:roku:ecp:X000003AFRLD',
     'wakeup': 'MAC=f0:a3:b2:03:db:8f;Timeout=10'},
    {'cache-control': 'max-age=3600',
     'device-group.roku.com': 'E3E7288623F19FA4030E',
     'ext': '',
     'location': 'http://192.168.58.108:8060/',
     'server': 'Roku/15.1.4 UPnP/1.0 Roku/15.1.4',
     'st': 'roku:ecp',
     'usn': 'uuid:roku:ecp:X0200065PNYN',
     'wakeup': 'MAC=78:66:9d:cc:eb:63;Timeout=10'}
)
for device in devices:
    mac, timeout = device['wakeup'].split(';')
    _, mac = mac.split('=')
    device['device_id'] = ''.join(mac.split(':'))

device_by_device_id = dict((device['device_id'], device) for device in devices)


@app.get(site_prefix + '/devices')
async def get_devices():
    # xmltodict.parse
    return dict(devices=devices)


client = httpx.AsyncClient()

@app.post(site_prefix + '/devices/{device_id}/keypress/{key_name}')
async def get_device_keypress(device_id: str, key_name: str):
    device = device_by_device_id.get(device_id)
    location = device['location']
    response = await client.post(f'{location}keypress/{key_name}', data='')
    return dict(
        response = str(response),
    )

    return dict(
        function = 'post_device_keypress',
        site_id = site_id,
        device_id = device_id,
        key_name = key_name,
        location = location,
        r = str(r),
    )


# http://192.168.23.10:8000/keypress/192.168.58.108:8060/Home
@app.post('/keypress/{location}/{key_name}')
async def get_location_keypress(location: str, key_name: str):
    #device = device_by_device_id.get(device_id)
    #location = device['location']
    response = await client.post(f'http://{location}/keypress/{key_name}', data='')
    return dict(
        response = str(response),
    )
