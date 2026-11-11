import json
from pathlib import Path

# parents[0] = utils, [1] = app, [2] = backend
FILE = Path(__file__).resolve().parents[2] / 'products.json'

PRODUCTS = json.loads(FILE.read_text(encoding='utf-8'))
BY_ID = {p['id']: p for p in PRODUCTS}
for _p in PRODUCTS:
    _p.update({'image_url': None, 'merchant': None, 'buy_url': None, 'source': 'sample'})


def public(p):
    '''What the website and the AI see (no search tags).'''
    return {k: v for k, v in p.items() if k != 'tags'}
