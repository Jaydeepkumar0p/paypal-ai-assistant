"""One place for product search. Uses Channel3 when a key is set, and falls back to the built-in
sample catalog if Channel3 is unavailable (so the store always works)."""
import asyncio
import re
from decimal import Decimal

from app.services import channel3
from app.utils.products import PRODUCTS, public

# "Shelves" are the store's categories. With Channel3 each one is a search; with the sample data it is a filter.
SHELVES = [
    {'name': 'Audio', 'tag': 'audio', 'emoji': '🎧', 'query': 'wireless headphones and bluetooth speakers'},
    {'name': 'Computing', 'tag': 'computer', 'emoji': '💻', 'query': 'computer keyboards, mice and laptop accessories'},
    {'name': 'Mobile', 'tag': 'phone', 'emoji': '📱', 'query': 'phone chargers, power banks and cases'},
    {'name': 'Wearables', 'tag': 'wearable', 'emoji': '⌚', 'query': 'smartwatches and fitness trackers'},
    {'name': 'Gaming', 'tag': 'gaming', 'emoji': '🎮', 'query': 'gaming controllers and headsets'},
    {'name': 'Smart Home', 'tag': 'smart home', 'emoji': '🏠', 'query': 'smart home devices and smart plugs'},
]
CATEGORIES = [s['name'] for s in SHELVES]
SHELF_BY_NAME = {s['name'].lower(): s for s in SHELVES}

PRODUCT_CACHE = {p['id']: public(p) for p in PRODUCTS}      # id -> product, filled by every search

STOPWORDS = {
    'show', 'me', 'find', 'some', 'the', 'any', 'want', 'need', 'for', 'please', 'search', 'looking',
    'buy', 'get', 'and', 'with', 'have', 'you', 'what', 'do', 'does', 'something', 'your', 'everything',
    'all', 'products', 'product', 'catalog', 'store', 'items', 'item', 'available', 'gear', 'stuff',
    'under', 'over', 'below', 'above', 'less', 'more', 'than', 'best', 'good', 'top', 'cheap',
    'cheapest', 'budget', 'nice', 'great', 'like', 'that', 'this', 'are', 'can', 'from', 'into',
    'recommend', 'suggest', 'about', 'around', 'new', 'one', 'ones', 'deal', 'deals', 'sale',
}


def stem(w):
    return w[:-1] if len(w) > 3 and w.endswith('s') and not w.endswith('ss') else w


def tokens(text):
    return {stem(w) for w in re.findall(r'[a-z0-9]+', text.lower())}


def query_words(q):
    return [stem(w) for w in re.findall(r'[a-z0-9]+', (q or '').lower()) if len(w) >= 3 and w not in STOPWORDS]


def price(p):
    return Decimal(p['price'])


def discount_pct(p):
    if not p.get('original_price'):
        return 0
    o, n = Decimal(p['original_price']), price(p)
    return int(round((o - n) / o * 100))


# ---------------------------------------------------------------- sample catalog
def head_noun(p):
    name = re.sub(r'\(.*?\)', ' ', p['name'])
    parts = re.findall(r'[a-z0-9]+', name.lower())
    return stem(parts[-1]) if parts else ''


def _score(p, words):
    name, brand = tokens(p['name']), tokens(p['brand'])
    tags, cat = tokens(' '.join(p['tags'])), tokens(p['category'])
    desc = tokens(p['description'] + ' ' + ' '.join(p['features']))
    head = head_noun(p)
    s = 0
    for w in words:
        s += 3 * (w in name) + 3 * (w in brand) + 2 * (w in tags) + 2 * (w in cat) + (w in desc) + 4 * (w == head)
    return s


def _matched(p, words):
    fields = tokens(' '.join([p['name'], p['brand'], p['category'], p['description'],
                              ' '.join(p['features']), ' '.join(p['tags'])]))
    return sum(1 for w in words if w in fields)


def sample_search(q, categories, min_price, max_price, on_sale):
    cats = {c.lower() for c in (categories or [])}
    words = query_words(q)
    rows = []
    for p in PRODUCTS:
        if cats and p['category'].lower() not in cats:
            continue
        if min_price is not None and price(p) < Decimal(str(min_price)):
            continue
        if max_price is not None and price(p) > Decimal(str(max_price)):
            continue
        if on_sale and discount_pct(p) <= 0:
            continue
        score = _score(p, words) if words else 0
        if words and score == 0:
            continue
        rows.append((score, p))
    if len(words) > 1:
        full = [r for r in rows if _matched(r[1], words) == len(words)]
        rows = full or rows
    rows.sort(key=lambda r: (-r[0], -r[1]['reviews']))
    return [public(p) for _, p in rows]


# ---------------------------------------------------------------- Channel3
async def live_search(q, categories, min_price, max_price, on_sale, user_id):
    filters = {'availability': ['InStock']}
    rng = {}
    if min_price is not None:
        rng['min_price'] = float(min_price)
    if max_price is not None:
        rng['max_price'] = float(max_price)
    if rng:
        filters['price'] = rng
    if on_sale:
        filters['sale'] = 'on_sale'

    shelves = [SHELF_BY_NAME[c.lower()] for c in categories if c.lower() in SHELF_BY_NAME]
    if shelves:
        per = 30 if len(shelves) == 1 else max(10, 30 // len(shelves))
        jobs = [((q.strip() + ' ' + s['tag']).strip() if q.strip() else s['query'], per, s) for s in shelves]
    elif q.strip():
        jobs = [(q.strip(), 30, None)]
    else:                                       # home page: a little of every shelf
        jobs = [(s['query'], 6, s) for s in SHELVES]

    results = await asyncio.gather(*[
        channel3.search(query, filters, n, user_id, s['emoji'] if s else '🛍️', s['name'] if s else None)
        for query, n, s in jobs
    ])
    seen, merged = set(), []
    for i in range(max((len(r) for r in results), default=0)):   # round-robin so every shelf shows up
        for r in results:
            if i < len(r) and r[i]['stock'] > 0 and r[i]['id'] not in seen:
                seen.add(r[i]['id'])
                merged.append(r[i])
    return merged[:30]


# ---------------------------------------------------------------- shared
def brand_counts(items):
    counts = {}
    for p in items:
        counts[p['brand']] = counts.get(p['brand'], 0) + 1
    return [{'name': k, 'count': v} for k, v in sorted(counts.items())]


def apply_post(items, brands, min_rating, in_stock, sort):
    brs = {b.lower() for b in brands or []}
    out = [p for p in items
           if (not brs or p['brand'].lower() in brs)
           and (not min_rating or (p.get('rating') or 0) >= float(min_rating))
           and (not in_stock or p['stock'] > 0)]
    keys = {
        'price_asc': lambda p: price(p),
        'price_desc': lambda p: -price(p),
        'rating': lambda p: -(p.get('rating') or 0),
        'reviews': lambda p: -(p.get('reviews') or 0),
        'discount': lambda p: -discount_pct(p),
    }
    return sorted(out, key=keys[sort]) if sort in keys else out


async def search(q='', categories=None, brands=None, min_price=None, max_price=None, min_rating=0,
                 in_stock=False, on_sale=False, sort='featured', limit=None, user_id=None):
    '''Returns {'items', 'brands', 'source'}. brands lists the brands in the results BEFORE the brand filter.'''
    categories = categories or []
    items, source = None, 'sample'
    if channel3.enabled():
        try:
            items = await live_search(q, categories, min_price, max_price, on_sale, user_id)
            source = 'channel3'
        except channel3.Channel3Error as e:
            print('Channel3 problem, using the sample catalog:', e)
    if items is None:
        items = sample_search(q, categories, min_price, max_price, on_sale)
    for p in items:
        PRODUCT_CACHE[p['id']] = p
    brand_list = brand_counts(items)
    items = apply_post(items, brands, min_rating, in_stock, sort)
    return {'items': items[:limit] if limit else items, 'brands': brand_list, 'source': source}


async def get_product(product_id, user_id=None):
    '''Cache first, then Channel3 (free). None if it does not exist.'''
    if product_id in PRODUCT_CACHE:
        return PRODUCT_CACHE[product_id]
    if channel3.enabled():
        try:
            p = await channel3.retrieve(product_id, user_id)
        except channel3.Channel3Error:
            return None
        if p:
            PRODUCT_CACHE[product_id] = p
        return p
    return None


def facets():
    if channel3.enabled():
        return {'categories': [{'name': s['name'], 'count': None} for s in SHELVES],
                'brands': [], 'price': {'min': 0, 'max': 500}, 'source': 'channel3'}
    cats = {}
    for p in PRODUCTS:
        cats[p['category']] = cats.get(p['category'], 0) + 1
    prices = [price(p) for p in PRODUCTS]
    return {'categories': [{'name': s['name'], 'count': cats.get(s['name'], 0)} for s in SHELVES],
            'brands': brand_counts(PRODUCTS), 'price': {'min': int(min(prices)), 'max': int(max(prices)) + 1},
            'source': 'sample'}


async def build_bundle(budget, needs, user_id=None):
    '''Pick one good in-stock product per need, staying inside the budget.'''
    remaining = Decimal(str(budget))
    start = remaining
    chosen, unmet = [], []
    for i, need in enumerate(needs):
        found = (await search(need, in_stock=True, limit=8, user_id=user_id))['items']
        cands = [p for p in found[:6] if p['id'] not in {c['id'] for c in chosen}]   # top results = most relevant
        within = [p for p in cands if price(p) <= remaining]
        if not within:
            unmet.append(need)
            continue
        share = remaining / (len(needs) - i) * Decimal('1.5')
        good = [p for p in within if price(p) <= share] or within
        pick = max(good, key=lambda p: (p.get('rating') or 3.5, -price(p)))
        chosen.append({**pick, 'need': need})
        remaining -= price(pick)
    total = start - remaining
    return {'items': chosen, 'total': f'{total:.2f}', 'budget': f'{start:.2f}', 'left': f'{remaining:.2f}', 'unmet': unmet}


async def search_and_remember(session, **kw):
    items = (await search(user_id=session.get('id'), **kw))['items']
    if items:
        session['last_product'] = items[0]['id']
    return items


def resolve_product_id(session, product_id=''):
    return product_id or session['last_product']
