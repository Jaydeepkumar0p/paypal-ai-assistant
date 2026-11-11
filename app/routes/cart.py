from fastapi import APIRouter, HTTPException

from app.models.schemas import AddIn, CartSetIn, SessionIn
from app.services.cart import add_item, cart_view, set_qty
from app.services import catalog
from app.utils import store

router = APIRouter()


@router.get('/cart/{session_id}')
async def get_cart(session_id: str):
    return cart_view(store.get_session(session_id))


@router.post('/cart/add')
async def cart_add(body: AddIn):
    session = store.get_session(body.session_id)
    product = await catalog.get_product(body.product_id, body.session_id)
    if not product:
        raise HTTPException(404, 'Unknown product')
    try:
        add_item(session, product, body.quantity)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return cart_view(session)


@router.post('/cart/set')
async def cart_set(body: CartSetIn):
    session = store.get_session(body.session_id)
    try:
        set_qty(session, body.product_id, body.quantity)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return cart_view(session)


@router.post('/cart/clear')
async def cart_clear(body: SessionIn):
    session = store.get_session(body.session_id)
    session['cart'] = []
    return cart_view(session)
