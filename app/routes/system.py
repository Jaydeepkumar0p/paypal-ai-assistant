from fastapi import APIRouter

from app.services import channel3
from app.utils import config

router = APIRouter()


@router.get('/health')
def health():
    return {'status': 'success', 'message': 'PayPilot is healthy'}


@router.get('/config')
def public_config():
    '''Values the website needs. The PayPal client id is public by design. The secret never leaves the server.'''
    return {'app': 'PayPilot', 'paypal_client_id': config.PAYPAL_CLIENT_ID, 'currency': config.PAYPAL_CURRENCY,
            'catalog_source': 'channel3' if channel3.enabled() else 'sample'}
