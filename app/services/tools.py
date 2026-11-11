"""Tools the AI can call. The AI helps people shop (search, filter, compare, recommend, add to cart).
It can NOT pay: payment is the shopper pressing the PayPal button at Checkout."""
import json

from langchain_core.tools import tool

from app.services import catalog
from app.services.cart import add_item, cart_view, set_qty
from app.services.help import HELP_TEXT
from app.utils.products import public


def j(data):
    return json.dumps(data)


def brief(p):
    return {k: p.get(k) for k in ('id', 'name', 'brand', 'price', 'original_price', 'category', 'rating', 'reviews', 'stock', 'merchant')}


def make_tools(session, ui):
    '''Build the tools for ONE shopper, so they can see this shopper session.'''
    uid = session.get('id')

    def ids_or_last(product_ids):
        ids = [p for p in (product_ids or []) if p]
        if not ids:
            pid = catalog.resolve_product_id(session)
            if not pid:
                return [], 'No product selected. Ask which product they mean.'
            ids = [pid]
        return ids, None

    @tool
    async def find_products(query: str = '', category: str = '', brand: str = '',
                            min_price: float | None = None, max_price: float | None = None,
                            min_rating: float = 0, in_stock_only: bool = False, on_sale: bool = False,
                            sort: str = 'featured', limit: int = 6, apply_to_store: bool = True) -> str:
        '''Search and filter the catalog. query is free text (for example headphones). category must be one of the store categories. sort is one of featured, price_asc, price_desc, rating, reviews, discount. Use max_price for under $X, on_sale for deals, min_rating for well rated. apply_to_store=true also filters the store page the shopper is looking at.'''
        cats = [c.strip() for c in category.split(',') if c.strip()]
        bad = [c for c in cats if c.lower() not in {x.lower() for x in catalog.CATEGORIES}]
        if bad:
            return j({'error': 'Unknown category ' + ', '.join(bad), 'valid_categories': catalog.CATEGORIES})
        brands = [b.strip() for b in brand.split(',') if b.strip()]
        results = await catalog.search_and_remember(
            session, q=query, categories=cats, brands=brands, min_price=min_price, max_price=max_price,
            min_rating=min_rating, in_stock=in_stock_only, on_sale=on_sale, sort=sort,
            limit=max(1, min(limit, 12)))
        ui['products'] = results
        if apply_to_store:
            ui['filters'] = {'query': query, 'category': cats, 'brand': brands, 'min_price': min_price,
                             'max_price': max_price, 'min_rating': min_rating, 'in_stock': in_stock_only,
                             'on_sale': on_sale, 'sort': sort}
        return j({'count': len(results), 'products': [brief(p) for p in results]})

    @tool
    async def get_product(product_id: str = '') -> str:
        '''Get full details of one product. Leave product_id empty for this or it.'''
        ids, err = ids_or_last([product_id] if product_id else [])
        if err:
            return j({'error': err})
        p = await catalog.get_product(ids[0], uid)
        if not p:
            return j({'error': 'Unknown product id.'})
        session['last_product'] = p['id']
        ui['products'] = [p]
        return j(p)

    @tool
    async def compare_products(product_ids: list[str]) -> str:
        '''Compare 2 to 4 products side by side by id. The app shows a comparison table.'''
        found = [await catalog.get_product(i, uid) for i in product_ids[:4]]
        items = [p for p in found if p]
        if len(items) < 2:
            return j({'error': 'Need at least two valid product ids to compare.'})
        ui['compare'] = items
        cheapest = min(items, key=lambda p: float(p['price']))
        best_rated = max(items, key=lambda p: p.get('rating') or 0)
        return j({'products': [brief(p) | {'features': p['features']} for p in items],
                  'cheapest': cheapest['id'], 'best_rated': best_rated['id'] if best_rated.get('rating') else None})

    @tool
    async def build_bundle(budget: float, needs: list[str]) -> str:
        '''Build a bundle that fits a budget. needs is a list of things wanted, for example keyboard, mouse, laptop stand. Picks one well-rated in-stock product per need.'''
        b = await catalog.build_bundle(budget, needs, uid)
        ui['bundle'] = b
        ui['products'] = b['items']
        return j({'items': [brief(p) | {'need': p['need']} for p in b['items']], 'total': b['total'],
                  'budget': b['budget'], 'left': b['left'], 'not_found_within_budget': b['unmet']})

    @tool
    async def add_to_cart(product_ids: list[str] | None = None, quantity: int = 1) -> str:
        '''Add one or more products to the cart by id. Pass every id when several are wanted. For this or it, leave product_ids empty.'''
        ids, err = ids_or_last(product_ids)
        if err:
            return j({'error': err})
        added, problems = [], []
        for pid in ids:
            p = await catalog.get_product(pid, uid)
            if not p:
                problems.append('Unknown product id ' + pid)
                continue
            try:
                add_item(session, p, max(1, quantity))
                added.append(p['name'])
            except ValueError as e:
                problems.append(str(e))
        c = cart_view(session)
        return j({'added': added, 'problems': problems, 'cart_total': c['total'], 'cart_count': c['count']})

    @tool
    def remove_from_cart(product_ids: list[str] | None = None) -> str:
        '''Remove products from the cart by id. For this or it, leave product_ids empty.'''
        ids, err = ids_or_last(product_ids)
        if err:
            return j({'error': err})
        for pid in ids:
            set_qty(session, pid, 0)
        c = cart_view(session)
        return j({'cart_total': c['total'], 'cart_count': c['count']})

    @tool
    def clear_cart() -> str:
        '''Remove everything from the cart.'''
        session['cart'] = []
        return j({'cart_count': 0})

    @tool
    def view_cart() -> str:
        '''Show the cart contents, shipping and total.'''
        c = cart_view(session)
        return j({'items': [{'id': i['id'], 'name': i['name'], 'qty': i['qty'], 'line_total': i['line_total']}
                            for i in c['items']],
                  'subtotal': c['subtotal'], 'shipping': c['shipping'], 'total': c['total'],
                  'free_shipping_remaining': c['free_shipping_remaining']})

    @tool
    def open_cart(target: str = 'cart') -> str:
        '''Open the cart drawer (target=cart) or the checkout page (target=checkout) for the shopper. You cannot pay: the shopper finishes with the PayPal button.'''
        ui['navigate'] = 'checkout' if target == 'checkout' else 'cart'
        return j({'opened': ui['navigate']})

    @tool
    def list_orders() -> str:
        '''List the shopper orders and their status (read only).'''
        return j({'orders': [{'id': o['id'], 'status': o['status'], 'total': o['total'],
                              'items': [i['name'] + ' x' + str(i['qty']) for i in o['items']]}
                             for o in session['orders']]})

    @tool
    def store_help(question: str) -> str:
        '''Use for questions about shipping, payment, order statuses, returns or what the assistant can do.'''
        return HELP_TEXT

    return [find_products, get_product, compare_products, build_bundle, add_to_cart, remove_from_cart,
            clear_cart, view_cart, open_cart, list_orders, store_help]
