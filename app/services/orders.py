from datetime import datetime, timezone

from app.services.cart import cart_view


def clean_customer(raw):
    c = {k: str(raw.get(k, '')).strip()[:120] for k in ('name', 'email', 'address', 'city', 'zip', 'country')}
    if not c['name'] or '@' not in c['email'] or not c['address']:
        raise ValueError('Please enter your name, a valid email and your address.')
    return c


def create_order(session, customer):
    '''Turn the cart into a pending order. Older pending orders are cancelled so there are no duplicates.'''
    cart = cart_view(session)
    if not cart['items']:
        raise ValueError('Your cart is empty.')
    customer = clean_customer(customer)
    for o in session['orders']:
        if o['status'] == 'pending':
            o['status'] = 'cancelled'
    session['order_seq'] += 1
    order = {
        'id': 'ORD-' + str(session['order_seq']),
        'items': [{k: i[k] for k in ('id', 'name', 'emoji', 'price', 'qty', 'line_total')} for i in cart['items']],
        'subtotal': cart['subtotal'],
        'shipping': cart['shipping'],
        'total': cart['total'],
        'status': 'pending',
        'customer': customer,
        'paypal_order_id': None,
        'capture_id': None,
        'created_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }
    session['orders'].append(order)
    return order


def find_by_paypal_id(session, paypal_order_id):
    for o in session['orders']:
        if o['paypal_order_id'] == paypal_order_id and o['status'] == 'pending':
            return o
    return None
