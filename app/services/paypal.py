"""PayPal sandbox: Orders v2 (create and capture)."""
import time
import uuid
from decimal import Decimal

import httpx

from app.utils import config

BASE_URL = 'https://api-m.sandbox.paypal.com'
_token = {'value': None, 'expires_at': 0.0}


class PayPalError(Exception):
    pass


async def get_access_token():
    if _token['value'] and time.time() < _token['expires_at'] - 60:
        return _token['value']
    if not config.PAYPAL_CLIENT_ID or not config.PAYPAL_CLIENT_SECRET:
        raise PayPalError('PayPal keys are not set on the server')
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                BASE_URL + '/v1/oauth2/token',
                auth=(config.PAYPAL_CLIENT_ID, config.PAYPAL_CLIENT_SECRET),
                data={'grant_type': 'client_credentials'},
            )
    except httpx.HTTPError as e:
        raise PayPalError('Could not reach PayPal: ' + type(e).__name__)
    if r.status_code != 200:
        raise PayPalError('PayPal auth failed: ' + r.text)
    data = r.json()
    _token['value'] = data['access_token']
    _token['expires_at'] = time.time() + int(data.get('expires_in', 300))
    return _token['value']


async def request(method, path, body=None):
    token = await get_access_token()
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json',
        'PayPal-Request-Id': uuid.uuid4().hex,
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.request(method, BASE_URL + path, headers=headers, json=body)
    except httpx.HTTPError as e:
        raise PayPalError('Could not reach PayPal: ' + type(e).__name__)
    if r.status_code >= 400:
        raise PayPalError('PayPal ' + str(r.status_code) + ': ' + r.text)
    return r.json()


def capture_id(data):
    try:
        return data['purchase_units'][0]['payments']['captures'][0]['id']
    except (KeyError, IndexError, TypeError):
        return None


async def create_order(items, shipping='0.00'):
    '''items: [{'name', 'price', 'qty'}]. Item total + shipping must equal the order total.'''
    cur = config.PAYPAL_CURRENCY
    item_total = Decimal('0')
    pp_items = []
    for it in items:
        p = Decimal(it['price'])
        item_total += p * it['qty']
        pp_items.append({
            'name': it['name'][:127],
            'quantity': str(it['qty']),
            'unit_amount': {'currency_code': cur, 'value': f'{p:.2f}'},
        })
    ship = Decimal(shipping)
    total = item_total + ship
    body = {
        'intent': 'CAPTURE',
        'purchase_units': [{
            'description': 'PayPilot order',
            'items': pp_items,
            'amount': {
                'currency_code': cur,
                'value': f'{total:.2f}',
                'breakdown': {
                    'item_total': {'currency_code': cur, 'value': f'{item_total:.2f}'},
                    'shipping': {'currency_code': cur, 'value': f'{ship:.2f}'},
                },
            },
        }],
    }
    data = await request('POST', '/v2/checkout/orders', body)
    return {'order_id': data['id'], 'status': data['status'], 'total': f'{total:.2f}', 'currency': cur}


async def capture_order(order_id):
    return await request('POST', '/v2/checkout/orders/' + order_id + '/capture', {})
