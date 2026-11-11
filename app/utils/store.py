import uuid

_sessions = {}


def new_session_id():
    return uuid.uuid4().hex


def get_session(session_id):
    return _sessions.setdefault(session_id, {
        'id': session_id,
        'cart': [],            # [{'product_id': 'p1', 'qty': 1}]
        'last_product': None,  # what "this" / "it" means
        'history': [],         # recent chat messages for the AI
        'orders': [],          # this shopper's orders
        'order_seq': 0,        # makes ORD-1, ORD-2, ...
    })
