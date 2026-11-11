# PayPilot: an online store with an AI shopping assistant and PayPal checkout

A real-looking electronics store (search, filters, sorting, product pages, cart, checkout) with an AI assistant that shops with you. The assistant finds and compares products, builds bundles for your budget, **filters the store for you** and **adds things to your cart**. You check out with **PayPal** (sandbox, no real money).

> The assistant can **not** pay. Paying is the normal PayPal button at Checkout.

## Features

**Store**
- Server-side search with relevance ranking, category, brand, price range, rating, in-stock and on-sale filters, six sort options
- Product quick view, sale and low-stock badges, loading skeletons, empty states
- Cart drawer with quantity steppers, shipping and a free-shipping progress bar (free over $75, otherwise $5.99)
- Checkout form with validation, then the PayPal button, a confirmation page and an orders page

**AI assistant** (Groq through LangChain, with eleven tools)
| Ask | What it does |
|---|---|
| "Best headphones under $60" | Searches with the right filters **and applies them to the store page** |
| "Compare the Aero headphones and the Pulse earbuds" | Shows a side-by-side table with the best price and rating marked |
| "Build me a work-from-home setup under $200" | Picks one well-rated in-stock product per need inside the budget, with an Add all button |
| "Show me the best deals" | Filters to sale items, sorted by discount |
| "Add the first one" / "add the cheapest" | Adds to the cart; it remembers the products it just showed |
| "What is in my cart?" / "Take me to checkout" | Reads the cart / opens the checkout page |
| "How does shipping work?" | Answers from the store info text |

**PayPal (sandbox):** Orders v2 create and capture, including shipping in the amount breakdown, with PayPal JS SDK buttons.

## Tools and services

| Tool | Used for |
|---|---|
| PayPal Developer (sandbox) | Orders v2 and JS SDK buttons |
| Groq + LangChain | LLM tool calling |
| FastAPI | API and web server (one service serves the API and the site) |
| React, Vite, Tailwind, Zustand | Frontend, with separate stores for shop, cart, assistant, orders, UI and session |
| Render | Hosting (`render.yaml`) |
| Postman | Collection in `postman/` to test every endpoint |

## Structure (monolith)

```
backend/                 FastAPI. Also serves the built site from static/
├── main.py
├── products.json        24 sample products (swap this for a real catalog later)
├── app/
│   ├── models/          request shapes
│   ├── utils/           config, sessions, products, LLM client
│   ├── routes/          system, products, cart, chat, checkout
│   └── services/        cart, catalog (search and filters), orders, paypal, tools, agent
└── static/              the built React site (committed, so deploys need no Node)
frontend/                React source
└── src/{stores,components,lib}
postman/                 Postman collection
render.yaml              Render blueprint
```

## Run locally

1. **Backend** (Python 3.10+), in `backend/`:
   ```bash
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env               # then fill in the keys
   uvicorn main:app --reload
   ```
   Open **http://localhost:8000**. The built site is already included.
2. **Frontend development** (only if you change the React code), in `frontend/`:
   ```bash
   npm install
   npm run dev                        # http://localhost:5173, proxies the API to :8000
   npm run build                      # writes the site into ../backend/static
   ```
3. **Pay as a test buyer:** in the PayPal dashboard go to Testing Tools > Sandbox Accounts and use the **Personal** account's email and password in the PayPal window (private browser window).

## Environment variables

| Variable | Required | Note |
|---|---|---|
| `GROQ_API_KEY` | yes | Secret |
| `GROQ_MODEL` | no | Default `openai/gpt-oss-120b` |
| `PAYPAL_CLIENT_ID` | yes | Sandbox client id (public, the site needs it) |
| `PAYPAL_CLIENT_SECRET` | yes | Sandbox secret. Server only |
| `PAYPAL_CURRENCY` | no | `USD` |
| `PYTHON_VERSION` | Render | `3.12.7` |

## Deploy on Render

1. Push to a public GitHub repo (never commit `.env`).
2. Render > **New > Blueprint** > pick the repo. It reads `render.yaml`.
3. Enter `GROQ_API_KEY`, `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` when asked.
4. Open the service URL. Free instances sleep when idle, so open the page a minute before a demo.

## Demo script (about 2 minutes)

1. Browse: click **Audio**, filter **Under $100**, sort by **Top rated**.
2. Open the assistant: "best headphones under $60" (the store filters itself).
3. "Compare the Aero headphones and the Pulse earbuds".
4. "Build me a work-from-home setup under $200", click **Add all**.
5. Open the cart (watch the free-shipping bar), click **Checkout**, fill the form.
6. Pay with the PayPal button as the sandbox buyer, then show the confirmation and Orders page.

## Honest limits

- Sandbox only. Carts, orders and chats live in server memory and reset on restart or sleep.
- No login: each browser gets a random session id.
- Products are sample data. Real product data (for example Channel3) is a planned next step; the catalog and filters already live behind one service layer (`services/catalog.py`).
- The assistant can misunderstand, which is why it never pays and checkout is a normal PayPal flow.

## License

MIT, see `LICENSE`.
