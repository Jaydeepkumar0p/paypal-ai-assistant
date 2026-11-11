from decimal import Decimal

from app.utils.products import public

MAX_QTY = 10
SHIPPING_FLAT = Decimal('5.99')
FREE_SHIPPING_OVER = Decimal('75.00')


def money(v):
    return f'{v:.2f}'


def shipping_for(subtotal):
    if subtotal <= 0 or subtotal >= FREE_SHIPPING_OVER:
        return Decimal('0')
    return SHIPPING_FLAT


def add_item(session, product, qty=1):
    '''product is a full product dict (from the catalog). A snapshot is kept so the cart never
    depends on the catalog again. Raises ValueError with a friendly message.'''
    if product['stock'] <= 0:
        raise ValueError(product['name'] + ' is out of stock')
    limit = min(MAX_QTY, product['stock'])
    for line in session['cart']:
        if line['product_id'] == product['id']:
            line['qty'] = min(line['qty'] + max(1, qty), limit)
            break
    else:
        session['cart'].append({'product_id': product['id'], 'qty': min(max(1, qty), limit), 'snap': public(product)})
    session['last_product'] = product['id']


def set_qty(session, product_id, qty):
    if qty <= 0:
        session['cart'] = [c for c in session['cart'] if c['product_id'] != product_id]
        return
    for line in session['cart']:
        if line['product_id'] == product_id:
            line['qty'] = min(qty, MAX_QTY, line['snap']['stock'])
            return
    raise ValueError('That item is not in your cart')


def cart_view(session):
    items, subtotal, count = [], Decimal('0'), 0
    for line in session['cart']:
        p = line['snap']
        line_total = Decimal(p['price']) * line['qty']
        subtotal += line_total
        count += line['qty']
        items.append({**p, 'qty': line['qty'], 'line_total': money(line_total)})
    shipping = shipping_for(subtotal)
    remaining = max(Decimal('0'), FREE_SHIPPING_OVER - subtotal)
    return {
        'items': items,
        'count': count,
        'subtotal': money(subtotal),
        'shipping': money(shipping),
        'total': money(subtotal + shipping),
        'free_shipping_threshold': money(FREE_SHIPPING_OVER),
        'free_shipping_remaining': money(remaining),
    }
