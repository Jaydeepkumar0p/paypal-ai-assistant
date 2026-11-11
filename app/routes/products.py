from fastapi import APIRouter, Header, HTTPException

from app.services import catalog

router = APIRouter()


def split(value):
    return [v.strip() for v in value.split(',') if v.strip()]


@router.get('/products')
async def list_products(q: str = '', category: str = '', brand: str = '',
                        min_price: float | None = None, max_price: float | None = None,
                        min_rating: float = 0, in_stock: bool = False, on_sale: bool = False,
                        sort: str = 'featured', limit: int | None = None,
                        x_session_id: str | None = Header(default=None)):
    r = await catalog.search(q, split(category), split(brand), min_price, max_price, min_rating,
                             in_stock, on_sale, sort, limit, user_id=x_session_id)
    return {'items': r['items'], 'total': len(r['items']), 'brands': r['brands'], 'source': r['source']}


@router.get('/products/facets')
async def product_facets():
    return catalog.facets()


@router.get('/products/{product_id}')
async def product_detail(product_id: str, x_session_id: str | None = Header(default=None)):
    p = await catalog.get_product(product_id, x_session_id)
    if not p:
        raise HTTPException(404, 'Unknown product')
    return p
