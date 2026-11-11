from fastapi import APIRouter, HTTPException

from app.models.schemas import CaptureIn, CheckoutIn
from app.services import orders as ords
from app.services import paypal
from app.utils import store

router = APIRouter()


@router.get('/orders/{session_id}')
async def list_orders(session_id: str):
    return {'orders': store.get_session(session_id)['orders']}


@router.post('/checkout')
async def checkout(body: CheckoutIn):
    '''Called when the shopper presses the PayPal button: make the order and the PayPal order.'''
    session = store.get_session(body.session_id)
    try:
        order = ords.create_order(session, body.customer)
    except ValueError as e:
        raise HTTPException(400, str(e))
    items = [{'name': i['name'], 'price': i['price'], 'qty': i['qty']} for i in order['items']]
    try:
        pp = await paypal.create_order(items, order['shipping'])
    except paypal.PayPalError as e:
        order['status'] = 'cancelled'
        raise HTTPException(502, str(e))
    order['paypal_order_id'] = pp['order_id']
    return {'order': order, 'paypal': pp}


@router.post('/capture-order')
async def capture_order(body: CaptureIn):
    '''Called after the shopper approves in the PayPal window.'''
    session = store.get_session(body.session_id)
    order = ords.find_by_paypal_id(session, body.order_id)
    if not order:
        raise HTTPException(409, 'No pending order matches this PayPal payment.')
    try:
        data = await paypal.capture_order(body.order_id)
    except paypal.PayPalError as e:
        raise HTTPException(502, str(e))
    if data.get('status') != 'COMPLETED':
        raise HTTPException(402, 'Payment status: ' + str(data.get('status')))
    order['status'] = 'paid'
    order['capture_id'] = paypal.capture_id(data)
    session['cart'] = []
    return {'order': order}
