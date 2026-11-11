from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import cart, chat, checkout, products, system
from app.utils import config

app = FastAPI(
    title='PayPilot',
    description='An AI-assisted online store with PayPal checkout.',
    version='2.0.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.FRONTEND_ORIGIN.split(','),
    allow_methods=['*'],
    allow_headers=['*'],
)

# Controllers (API routes)
app.include_router(system.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(chat.router)
app.include_router(checkout.router)

# Views: the React site (built into backend/static), served by the same app. Mounted last so API routes win.
STATIC_DIR = Path(__file__).resolve().parent / 'static'
STATIC_DIR.mkdir(exist_ok=True)
app.mount('/', StaticFiles(directory=STATIC_DIR, html=True), name='site')
