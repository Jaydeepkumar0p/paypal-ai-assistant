<div align="center">

<img src="assets/paypilot-header.gif" alt="Animated PayPilot AI banner showing product search, AI comparison, and PayPal sandbox checkout" width="100%" />

# PayPilot AI

### Your AI-powered shopping copilot for real products

**Search smarter · Compare confidently · Build budget-friendly bundles · Check out with PayPal Sandbox**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-149ECA?style=for-the-badge&logo=react&logoColor=white)](https://react.dev/)
[![PayPal](https://img.shields.io/badge/PayPal-Sandbox-003087?style=for-the-badge&logo=paypal&logoColor=white)](https://developer.paypal.com/)

[![Groq](https://img.shields.io/badge/AI-Groq%20%2B%20LangChain-7C3AED?style=flat-square)](https://console.groq.com/)
[![Channel3](https://img.shields.io/badge/Catalog-Channel3%20API-13B8A6?style=flat-square)](https://docs.trychannel3.com/)
[![Render](https://img.shields.io/badge/Deploy-Render-5967D8?style=flat-square)](https://render.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

[Features](#-features) · [How it works](#-how-it-works) · [Quick start](#-quick-start) · [Channel3](#-channel3-live-product-catalog) · [API reference](#-api-reference) · [Deploy](#-deploy-on-render) · [Demo](#-demo-walkthrough)

</div>

> [!IMPORTANT]
> **Hackathon demonstration, not a live merchant.** Product information can come from real retailers through **Channel3**, but payments are made using the **PayPal Sandbox**. No real money is charged through this demo and **nothing is shipped**. The AI assistant **cannot complete payments** on a shopper's behalf.

## ✨ Overview

PayPilot AI combines a full-featured electronics storefront with a conversational shopping assistant. Instead of manually opening dozens of product pages, shoppers can ask natural-language questions, compare options, apply filters automatically, build a bundle within a budget, and add recommendations to their cart.

When `CHANNEL3_API_KEY` is configured, the store searches **live Channel3 product data**. If no key is configured, or a Channel3 request fails, the app uses a built-in **24-product sample catalog** so the demo remains usable.

### 🌟 Features

| 🛍️ Storefront | 🧠 AI shopping assistant | 💳 Checkout |
|---|---|---|
| Real product photos and retailer links when available | Understands natural-language shopping requests | PayPal Orders v2 (Sandbox) |
| Six electronics categories | Searches, compares and recommends products | PayPal JS SDK checkout button |
| Search, filters and six sort modes | Applies chat-requested filters to the store UI | Shipping included in order totals |
| Quick view, sale badges and loading states | Builds budget-aware bundles with an **Add all** action | Order confirmation and order history |
| Cart drawer and quantity controls | Adds/removes items and navigates to checkout | Sandbox payment capture |

**Store categories:** Audio · Computing · Mobile · Wearables · Gaming · Smart Home

**Sorting:** `featured`, `price_asc`, `price_desc`, `rating`, `reviews`, `discount`.

**Shipping in the demo:** Free when cart subtotal is **$75 or more**; otherwise **$5.99** for a non-empty cart.

## 🧠 Talk to the shopping assistant

The Groq-powered agent uses **LangChain tool calling** to interact with the **same catalog and cart services** as the store UI.

| Try asking… | What PayPilot does |
|---|---|
| `Find the best headphones under $60` | Searches products with a price limit and applies filters to the storefront |
| `Compare these two headphones` | Presents a side-by-side product comparison |
| `Build a work-from-home setup under $200` | Selects items for multiple needs within the budget, where possible |
| `Show me products on sale` | Applies the on-sale filter and sorts by discount |
| `Add the first one to my cart` | Uses the recently shown product context to add the item |
| `Remove that item from my cart` | Updates the session cart |
| `What's in my cart?` | Shows products, subtotal, shipping and total |
| `Take me to checkout` | Opens checkout; **you** must approve payment |

<details>
<summary><b>View all 11 AI tools</b></summary>

| Tool | Responsibility |
|---|---|
| `find_products` | Search and filter the catalog; optionally update store filters |
| `get_product` | Retrieve one product's details |
| `compare_products` | Compare two to four product IDs |
| `build_bundle` | Select products for requested needs within a budget |
| `add_to_cart` | Add selected products and quantities |
| `remove_from_cart` | Remove selected products |
| `clear_cart` | Empty the cart |
| `view_cart` | Read the current cart and totals |
| `open_cart` | Open cart drawer or checkout page |
| `list_orders` | Read the session's orders |
| `store_help` | Answer questions about the demo store |

The agent is limited to **six tool-calling iterations** per request. Tool output grounds product and cart facts; recommendations remain AI-generated and should be reviewed.

</details>

## 🧩 How it works

```text
                         ┌─────────────────────────┐
                         │      React storefront   │
                         │  Search · Cart · AI Chat │
                         └────────────┬────────────┘
                                      │ HTTP / JSON
                                      ▼
                         ┌─────────────────────────┐
                         │       FastAPI app       │
                         │    Same-origin server   │
                         └────────────┬────────────┘
                                      │
           ┌──────────────────────────┼───────────────────────────┐
           ▼                          ▼                           ▼
  ┌─────────────────┐      ┌────────────────────┐       ┌────────────────┐
  │ Catalog service │      │   AI agent         │       │ Cart / Orders  │
  │ Search & filters│◀─────│ Groq + LangChain   │──────▶│ Session memory │
  └────────┬────────┘      │    11 tools        │       └───────┬────────┘
           │               └────────────────────┘               │
    ┌──────┴───────┐                                            ▼
    ▼              ▼                                    ┌────────────────┐
┌──────────┐  ┌────────────┐                            │ PayPal Sandbox │
│ Channel3 │  │ 24 sample  │                            │ Orders v2      │
│ Products │  │  fallback  │                            └────────────────┘
└──────────┘  └────────────┘
```

**Single-service deployment:** FastAPI serves both the `/products`, `/cart`, `/chat` and checkout APIs **and** the pre-built React app in `backend/static/`. You do not need to deploy the frontend separately.

## 🗂️ Project structure

```text
paypilot-ai/
├── backend/
│   ├── main.py                      # FastAPI app and static mounting
│   ├── requirements.txt
│   ├── .env.example                 # Safe template for credentials
│   ├── products.json                # 24 fallback products
│   ├── app/
│   │   ├── models/schemas.py        # Pydantic request models
│   │   ├── routes/                  # HTTP endpoints
│   │   │   ├── system.py
│   │   │   ├── products.py
│   │   │   ├── cart.py
│   │   │   ├── chat.py
│   │   │   └── checkout.py
│   │   ├── services/
│   │   │   ├── channel3.py          # Channel3 API + TTL cache
│   │   │   ├── catalog.py           # Unified live / sample search
│   │   │   ├── agent.py             # LLM + tool execution loop
│   │   │   ├── tools.py             # 11 agent tools
│   │   │   ├── cart.py
│   │   │   ├── orders.py
│   │   │   └── paypal.py
│   │   └── utils/                   # Configuration and sessions
│   └── static/                      # Compiled React build
├── frontend/
│   ├── src/components/             # Store, assistant, checkout UI
│   ├── src/stores/                 # Zustand state modules
│   └── src/lib/                    # API client and formatting
├── postman/                         # Postman API collection
├── assets/paypilot-header.gif       # Animated README banner
├── render.yaml                      # Single Render web service
├── LICENSE
└── README.md
```

## 🚀 Quick start

**Requirements:** Python **3.10+**, pip, a Channel3 API key for real products, a Groq API key for the assistant and PayPal **sandbox** credentials for checkout. Node.js and npm are needed **only if you're changing the React source**.

### 1. Install and run the backend

**Windows PowerShell** (from the repository root):

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
uvicorn main:app --reload
```

**Windows Command Prompt (CMD):**

```bat
cd backend
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
copy .env.example .env
notepad .env
uvicorn main:app --reload
```

**macOS / Linux:**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env with your secret keys
uvicorn main:app --reload
```

> [!TIP]
> If `backend/.env` already exists, **do not overwrite it** with the copy command. Update the existing file instead. Run `uvicorn` from inside `backend/`.

### 2. Configure `backend/.env`

```dotenv
# AI assistant
GROQ_API_KEY=replace_with_your_groq_key
GROQ_MODEL=openai/gpt-oss-120b

# Live products (optional; without it the sample catalog is used)
CHANNEL3_API_KEY=replace_with_your_channel3_key
CATALOG_SOURCE=auto

# PayPal Developer Sandbox
PAYPAL_CLIENT_ID=replace_with_sandbox_client_id
PAYPAL_CLIENT_SECRET=replace_with_sandbox_client_secret
PAYPAL_CURRENCY=USD

# Same-origin frontend
FRONTEND_ORIGIN=*
FRONTEND_URL=http://localhost:8000
```

**Never commit `.env`, API keys or PayPal secrets to GitHub.** The repository's `.gitignore` excludes `.env`. If a credential is exposed, revoke/rotate it in the provider dashboard.

### 3. Open the app

- **Storefront:** http://localhost:8000
- **Interactive API docs:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

The compiled frontend is already stored under `backend/static/`.

### 4. Frontend development (optional)

Open a **second terminal** from the repository root:

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173; API proxied to :8000
npm run build        # writes the production site to ../backend/static
```

When changing the React UI for a single-service deployment, **run `npm run build` and commit the updated `backend/static/` output**.

## 🛒 Channel3 live product catalog

PayPilot uses Channel3 for real product titles, prices, available images, merchant details and retailer links. It is configured for **US products and USD prices**.

| Behavior | Implementation |
|---|---|
| Authentication | `x-api-key` request header |
| Live search | `POST https://api.trychannel3.com/v1/search` |
| Product lookup | `GET /v1/products/{product_id}` |
| Categories | Each of six shelves maps to a targeted product search |
| Homepage | Combines products across categories and deduplicates results |
| Provider-side filters | In-stock, price range and on-sale |
| App-side filters | Brand and minimum rating |
| App-side sorting | Featured, price up/down, rating, reviews and discount |
| Result cache | In-memory **15-minute TTL** for repeated identical searches |
| Failure mode | Falls back to the bundled 24-product catalog |

Search results contain a `source` field: **`channel3`** for successful live searches and **`sample`** for fallback. Product cards use real images and retailer links when those fields are supplied by Channel3. Some products have no rating, photo or retailer link, and the UI handles missing fields.

**Inventory note:** Channel3 availability is treated as in-stock/out-of-stock. Its response is **not** a trustworthy warehouse quantity; the app currently uses an internal placeholder quantity for available Channel3 products.

**Pricing note:** Product offers are normalized on the **server** and the browser does not send trusted prices for checkout. The current cart stores **price snapshots**; it does **not** guarantee a fresh retailer-price recheck immediately before PayPal payment.

**Credits:** Repeating a cached query avoids another Channel3 search call during the TTL, while different queries or filters may spend additional provider credits. Check the current limits in your own Channel3 account.

### Verify the live integration

While FastAPI is running, in **PowerShell**:

```powershell
# Configuration check (does not reveal the API key)
python -c "from app.services import channel3; print('Enabled:', channel3.enabled())"

# Actual product search (this confirms whether live results were returned)
(Invoke-RestMethod 'http://localhost:8000/products?sort=featured').source
```

Expected result with a successful API request:

```text
Enabled: True
channel3
```

To inspect a product safely:

```powershell
$r = Invoke-RestMethod 'http://localhost:8000/products?sort=featured'
$r.items | Select-Object -First 1 name,price,image_url,merchant,source
```

> `GET /config` and `GET /products/facets` can report Channel3 as *configured*. To verify that a **real search succeeded**, check `source` from `GET /products`.

## 🔌 API reference

The backend uses JSON request and response bodies. An **`x-session-id`** header is sent by the frontend on its requests, while cart/chat/checkout POST bodies also carry a `session_id`.

| Method | Endpoint | What it does |
|---|---|---|
| `GET` | `/health` | Server health |
| `GET` | `/config` | Public frontend configuration |
| `GET` | `/products` | Search, filter and sort products |
| `GET` | `/products/facets` | Categories, brands and price bounds |
| `GET` | `/products/{product_id}` | Product details |
| `GET` | `/cart/{session_id}` | View cart |
| `POST` | `/cart/add` | Add an item |
| `POST` | `/cart/set` | Update quantity (`0` removes an item) |
| `POST` | `/cart/clear` | Empty cart |
| `POST` | `/chat` | Send a message to the AI agent |
| `GET` | `/orders/{session_id}` | Session order history |
| `POST` | `/checkout` | Create a pending order and PayPal sandbox order |
| `POST` | `/capture-order` | Capture an approved PayPal sandbox order |

<details>
<summary><b>Product-search parameters and request examples</b></summary>

`GET /products` accepts:

| Parameter | Example | Meaning |
|---|---|---|
| `q` | `headphones` | Text search |
| `category` | `Audio` | Comma-separated shelf names |
| `brand` | `Sony` | Comma-separated brands among results |
| `min_price` / `max_price` | `20` / `100` | USD price bounds |
| `min_rating` | `4.0` | Minimum displayed rating |
| `in_stock` | `true` | Only available products |
| `on_sale` | `true` | Only sale products |
| `sort` | `price_asc` | One of the six supported sort values |
| `limit` | `10` | Limit returned items |

**Examples**:

```bash
# Search and filter
curl "http://localhost:8000/products?q=headphones&max_price=60&sort=rating"

# Read available categories
curl "http://localhost:8000/products/facets"

# Add an item (replace PRODUCT_ID with an id returned by /products)
curl -X POST http://localhost:8000/cart/add \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo-session","product_id":"PRODUCT_ID","quantity":1}'

# Chat with the shopping assistant
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo-session","message":"Find headphones under $60"}'
```

</details>

For more examples, use **Swagger UI** at `/docs` or import `postman/PayPilot.postman_collection.json` into Postman.

## 💳 PayPal sandbox checkout

1. Add products to the cart and fill in the checkout form.
2. Click the PayPal button. The backend creates a **pending** order and a PayPal **Orders v2** order.
3. Approve the payment using a **PayPal Sandbox Personal (buyer)** account.
4. The frontend asks the backend to capture the approved order.
5. After a successful capture, the session order is marked **paid** and the cart is cleared.

Set up Sandbox test accounts in the [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/). **No real payments, fulfillment or shipping occur.** The assistant can open checkout but **cannot trigger payment approval**.

## ☁️ Deploy on Render

This repository includes a `render.yaml` Blueprint for **one Python web service**.

1. Push the project to GitHub, without `.env` or other secrets.
2. In Render, choose **New → Blueprint** and select the repository.
3. Supply these secrets in Render's environment settings: `GROQ_API_KEY`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` and `CHANNEL3_API_KEY`.
4. Deploy. Render installs `backend/requirements.txt` and starts Uvicorn using `render.yaml`.
5. Open the service URL and confirm `/health`, `/products` and a PayPal sandbox test checkout.

`render.yaml` already configures Python **3.12.7**, USD currency and the Channel3 key placeholder. `CATALOG_SOURCE` defaults to `auto`; set it in Render only if you want to override that behavior.

> [!NOTE]
> On an instance that sleeps or restarts, **in-memory sessions, carts, orders and chat history reset**. Render deployments need the compiled `backend/static/` files committed to the repository.

## 🎬 Demo walkthrough

A useful **2–3 minute** product demo:

1. **Discover:** Open the store; show real Channel3 product photos and the “Product data by Channel3” footer.
2. **Search:** Choose Audio, set a price cap, and sort by top rating.
3. **AI shopping:** Ask `Find the best headphones under $60` and show the store filters updating.
4. **Compare & bundle:** Compare two items from the current results; then request a work-from-home bundle under $200 and use **Add all**.
5. **Cart:** Show item quantities, shipping and the free-shipping progress bar.
6. **Checkout:** Complete a PayPal **sandbox** payment and show confirmation plus order history.

When presenting, explain that **Channel3 supplies product discovery**, **Groq + LangChain power tool-using AI assistance**, and **PayPal handles sandbox checkout**.

## 🧰 Troubleshooting

<details>
<summary><b>Channel3 keeps showing sample products</b></summary>

1. Check `backend/.env` has `CHANNEL3_API_KEY` (**not** `CHANNEL3_API`).
2. Set `CATALOG_SOURCE=auto` and restart Uvicorn.
3. Run `python -c "from app.services import channel3; print(channel3.enabled())"` from `backend/`.
4. Check `GET /products` for `"source": "channel3"`.
5. If it returns `sample`, check the server console for `Channel3 problem, using the sample catalog:` followed by the HTTP error or connection reason.

`200 OK` alone does not prove Channel3 succeeded, because fallback results also return HTTP 200.

</details>

<details>
<summary><b>Frontend changes do not appear on port 8000</b></summary>

Run `npm run build` from `frontend/` to regenerate `backend/static/`, then refresh your browser. `npm run dev` runs the Vite development site separately on port 5173.

</details>

<details>
<summary><b>Groq chat or PayPal checkout fails</b></summary>

Confirm the relevant key names in `backend/.env`, restart the server, and inspect the server response. The Groq account/model must support tool calling; PayPal requires **sandbox** client credentials and a sandbox buyer account. Never paste credentials into an issue, screenshot or chat.

</details>

## ⚠️ Demo limitations

- **Not a real store:** PayPal Sandbox only; no physical items are shipped.
- **Temporary state:** Carts, chats and orders are stored in server memory, not a database.
- **No user accounts:** A browser-local session ID identifies each demo shopper.
- **External catalog variability:** Listings, prices, images, retailers and ratings depend on Channel3 responses and can change.
- **Price snapshots:** Cart/checkout totals use server-side stored product prices, which may become stale relative to the retailer.
- **Simplified stock display:** Available Channel3 products have a placeholder stock number, not a retailer quantity.
- **AI suggestions:** The assistant can make mistakes; it never has authority to complete payments.

## 📄 License

Released under the [MIT License](LICENSE).

<div align="center">

**Built to turn product discovery into a conversation.**

⭐ If this project helps you, consider starring the repository.

</div>
