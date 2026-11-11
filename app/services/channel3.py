"""Channel3 product catalog (https://docs.trychannel3.com). Real products from many retailers.

Auth is the x-api-key header. Search is POST /v1/search (max 30 results). Product detail is free.
Results are cached for 15 minutes so repeat views do not spend credits."""
import json
import time
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import quote

import httpx

from app.utils import config

BASE_URL = 'https://api.trychannel3.com'
CACHE_SECONDS = 900
_cache = {}


class Channel3Error(Exception):
    pass


def enabled():
    return bool(config.CHANNEL3_API_KEY) and config.CATALOG_SOURCE != 'sample'


async def _request(method, path, body=None, user_id=None):
    headers = {'x-api-key': config.CHANNEL3_API_KEY or '', 'Content-Type': 'application/json'}
    if user_id:
        headers['x-user-id'] = user_id          # lets Channel3 attribute buy-link clicks
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            r = await client.request(method, BASE_URL + path, headers=headers, json=body)
    except httpx.HTTPError as e:
        raise Channel3Error('Could not reach Channel3: ' + type(e).__name__)
    if r.status_code >= 400:
        raise Channel3Error('Channel3 ' + str(r.status_code) + ': ' + r.text[:200])
    return r.json()


def money(value):
    return f"{Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def normalize(p, emoji='🛍️', shelf=None):
    '''Turn a Channel3 product into the shape the store and the AI use. Returns None if it cannot be sold.'''
    offers = [o for o in (p.get('offers') or []) if (o.get('price') or {}).get('currency') == 'USD']
    if not offers:
        return None
    in_stock = [o for o in offers if o.get('availability') == 'InStock']
    best = min(in_stock or offers, key=lambda o: o['price']['price'])
    price = best['price']['price']
    compare = best['price'].get('compare_at_price')
    images = p.get('images') or []
    main = next((i for i in images if i.get('is_main_image')), images[0] if images else None)
    brands = p.get('brands') or []
    category = (p.get('category') or {}).get('title') or shelf or 'Shopping'
    ratings = p.get('ratings') or {}
    return {
        'id': p['id'],
        'name': p.get('title') or 'Product',
        'brand': brands[0]['name'] if brands else best.get('domain', 'Store'),
        'price': money(price),
        'original_price': money(compare) if compare and compare > price else None,
        'category': category,
        'emoji': emoji,
        'rating': round(ratings['value'], 1) if ratings.get('value') else None,
        'reviews': ratings.get('count') if ratings.get('value') else None,
        'stock': 25 if in_stock else 0,          # Channel3 says in or out of stock, not how many
        'description': (p.get('description') or '').strip()[:600],
        'features': (p.get('key_features') or [])[:4],
        'image_url': (main.get('cleaned_url') or main.get('url')) if main else None,
        'merchant': best.get('domain'),
        'buy_url': best.get('url'),
        'source': 'channel3',
    }


async def search(query, filters=None, limit=30, user_id=None, emoji='🛍️', shelf=None):
    body = {
        'query': query,
        'limit': max(1, min(limit, 30)),
        'filters': filters or {'availability': ['InStock']},
        'config': {'currency': 'USD', 'country': 'US'},
    }
    key = json.dumps(body, sort_keys=True)
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    data = await _request('POST', '/v1/search', body, user_id)
    items = [n for n in (normalize(p, emoji, shelf) for p in data.get('products', [])) if n]
    if len(_cache) > 300:
        _cache.clear()
    _cache[key] = (time.time(), items)
    return items


async def retrieve(product_id, user_id=None):
    '''Product detail is free. Used for cart and checkout so prices come from Channel3, not the browser.'''
    data = await _request('GET', '/v1/products/' + quote(product_id, safe=''), None, user_id)
    return normalize(data)
