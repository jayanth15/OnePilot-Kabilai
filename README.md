# OnePilot Kabilai — Dairy WhatsApp CRM

An AI-powered WhatsApp platform for **Kabilai Dairy**. Customers message the clinic's WhatsApp number to browse dairy products, check prices, confirm Chennai delivery, and submit enquiries. Staff manage products, delivery areas, and enquiries from a web dashboard.

## Stack

| Layer     | Tech                                                                  |
| --------- | --------------------------------------------------------------------- |
| Frontend  | TanStack Start (Vite + React Router), Tailwind CSS 4, shadcn/ui, HugeIcons |
| Backend   | FastAPI, SQLModel (SQLite), Pydantic AI v2, JWT, Argon2               |
| Auth      | Email/password login, platform admin seeding                          |
| WhatsApp  | Gupshup (webhook + client), mock mode toggle                          |

## Quick Start

**Backend:**

```bash
cd backend
uv venv
uv pip install -r requirements.txt
uv run python -m app.seed
uv run python -m app
```

**Frontend:**

```bash
cd frontend
npm ci
npm run dev
```

Login: `admin@onecorestack.com` / `password`

## WhatsApp flow

Customers opt-in with `hi`, `hello`, `namaste`, `start ai`, etc. The assistant (Pydantic AI) uses tools to serve real data from the database:

- `list_dairy_products` — available products + prices
- `get_product_price` — price for a named product
- `check_delivery_area` — does the courier deliver to a given Chennai area/pincode
- `create_enquiry_tool` — capture a customer enquiry (sends a WhatsApp confirmation)
- `find_enquiries_by_phone` — past enquiries
- `request_operator_handoff` — switch to a human agent

## Pages

- `/login` — authentication
- `/dashboard` — products, delivery areas, and enquiries summary
- `/products` — manage product catalog + prices
- `/delivery-areas` — manage Chennai delivery coverage
- `/enquiries` — CRM enquiries (new/contacted/converted/closed)
- `/chat` — WhatsApp-style chat with contacts and AI
- `/settings` — app + WhatsApp messaging status

## Configuration

Set the following in `backend/.env` (see `.env.example`):

- `GUPSHUP_API_KEY`, `GUPSHUP_APP_NAME`, `GUPSHUP_SOURCE_NUMBER`
- `GUPSHUP_MOCK=true` to test without sending real messages
- `AGENT_MODEL=test` for the deterministic test model, or an OpenRouter model for real replies

## Tests

```bash
cd backend
uv run python -m unittest discover -s tests -v
```

```bash
cd frontend
npm run typecheck
npm run lint
npm run build
```
