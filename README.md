# Digi Karigari

A responsive, AI-assisted marketplace for Indian artisans. This is a **college demonstration project**:
payments are simulated, sample data is fictional, and nothing here is production-ready.

- **Frontend:** React + Vite (`frontend/`)
- **Backend:** Python FastAPI (`backend/`)
- **Database:** SQLite (a single file), written with SQLAlchemy so it can move to PostgreSQL later
- **Images:** stored on local disk in `backend/uploads/`

---

## 1. Feature status (honest labels)

| Feature | Status | Notes |
|---|---|---|
| Home, catalog, product pages, artisan profiles | **Implemented** | |
| Buyer / artisan / admin accounts | **Implemented** | Simple token login, fine for a demo |
| Seller create / edit / delete listings with photos | **Implemented** | Safe upload checks (type, size, random names) |
| Admin approves / rejects artisans, Verified badge | **Implemented** | |
| Cart and checkout | **Implemented** | Payment itself is simulated (below) |
| Order history, status tracking, manual courier + tracking ID | **Implemented** | No courier API |
| Keyword search, category and price filters | **Implemented** | Simple text matching |
| Loading, empty, validation and error states | **Implemented** | |
| AI listing assistant | **Demo-only** until you add a key | Mock mode does *not* look at the photo. Live mode is wired for a vision model. Suggestions are never auto-published |
| Test payment | **Demo-only** | Success/fail switch. No card data, no real money |
| Similar products | **Demo-only** | Just "same category" |
| English / Hindi | **Demo-only** | First-visit language popup + navbar switch. Menus, buttons, headings and form labels are translated; seller-written text, AI text, server error messages and policy pages are English |
| Admin basic counts | **Demo-only** | A few totals only |
| Terms / privacy / shipping / refund pages | **Demo-only** | Placeholder text, not legal advice |
| Semantic search, smart recommendations | Planned | |
| AI photo-quality / category-match advisory checks | Planned | Advice only; admin decides |
| Buyer-artisan messaging, notifications | Planned | |
| Reviews, disputes, refunds, seller trust tiers | Planned | |
| Full admin dashboard and analytics | Planned | |

The same list is available in the running app at **/features**, and from the API at `GET /api/features`.
Planned endpoints (`/api/planned/...`) return **501 Not Implemented** on purpose.

Deliberately **not** included: blockchain, cryptocurrency, real payments, courier APIs, payouts.

---

## 2. Requirements

- Windows 10/11 with **Python 3.10 or newer** (check: `py --version`)
- **Node.js 18 or newer** (check: `node --version`)

---

## 3. Run it (Windows PowerShell)

Open **two** PowerShell windows.

### Window 1: backend

```powershell
cd digi-karigari\backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m app.seed --reset
uvicorn app.main:app --reload --port 8000
```

If PowerShell says scripts are disabled, run this once in that window, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Check it works: open http://127.0.0.1:8000/api/health (should show `{"status":"ok"}`) and
http://127.0.0.1:8000/docs (automatic API documentation).

### Window 2: frontend

```powershell
cd digi-karigari\frontend
npm install
npm run dev
```

Open **http://localhost:5173**. On your first visit a popup asks you to choose **English or हिन्दी**.

---

## 4. Demo accounts

Password for every account: `demo1234` (the Login page has quick-fill buttons).

| Role | Email |
|---|---|
| Admin | admin@digikarigari-demo.com |
| Buyer | buyer@digikarigari-demo.com |
| Artisan (approved, Verified) | meera@, ramesh@, fatima@ `digikarigari-demo.com` |
| Artisan (**pending**) | sanjay@digikarigari-demo.com |

All artisans and products are **fictional**. Product images are generated placeholders.

### Suggested demo script (5 minutes)

1. Browse the shop as a visitor: search, filter by category and price, open a product, switch language.
2. Log in as **sanjay@** (pending): the seller dashboard says "waiting for approval" and cannot add listings.
3. Log in as **admin@**: approve Sanjay. His carved elephant now appears in the shop with a Verified badge.
4. Log in as **meera@**: *New listing* > choose a photo > type notes such as "terracotta planter, hand painted" >
   **Get AI suggestions** > review > **Use these suggestions** > edit the text > tick the confirmation box > Publish.
5. Log in as **buyer@**: add items to the cart > Checkout > try *failed* payment, then *successful* payment.
6. Log back in as **meera@**: *Orders to ship* > mark as Shipped with courier name and tracking ID.
7. As **buyer@**: *My orders* shows the tracking details.

---

## 5. The AI listing assistant

Flow: artisan uploads a photo and types notes > `POST /api/ai/listing-assist` > backend returns **suggestions only**
(title, description, category, materials, tags, "please check" points) > the artisan sees them, clicks
*Use these suggestions*, edits the normal form, ticks a confirmation box, and only then publishes.
Nothing is published automatically.

- **Demo mode (default):** `AI_PROVIDER=mock`. Uses simple keyword rules on your notes. It **does not analyse the photo**, and the app says so on screen.
- **Live mode:** in `backend/.env` set

  ```
  AI_PROVIDER=anthropic
  ANTHROPIC_API_KEY=your-key-here
  AI_MODEL=claude-sonnet-5-5
  ```

  then restart the backend. The key stays on the backend; the frontend never sees it.
- **Another provider later:** write one function in `backend/app/ai_service.py` that takes `(image_bytes, media_type, notes, filename)` and returns the same dictionary, then add it to `LIVE_PROVIDERS`. The frontend does not change.
- AI output can be wrong. The artisan is responsible for the final text, which is why the review step exists.

---

## 6. What each file does

### Backend (`backend/app/`)

| File | Beginner-friendly explanation |
|---|---|
| `main.py` | Starts the web server, turns on CORS, serves uploaded images, and plugs in all the routers |
| `config.py` | Reads settings (secret key, database URL, AI key) from `.env` |
| `constants.py` | Lists shared by everything, e.g. allowed categories and order steps |
| `database.py` | Connects to the database; gives each request its own session |
| `models.py` | The database tables: users, artisan profiles, products, images, orders, order items |
| `security.py` | Hashes passwords and creates / checks login tokens |
| `deps.py` | "Who is calling?" and "are they allowed?" checks reused by routes |
| `uploads.py` | Safe image saving: checks real file type, size limit, random file names |
| `serializers.py` | Turns database objects into the JSON the frontend receives (one place = fewer mismatches) |
| `ai_service.py` | The AI assistant: mock mode and live mode behind one function |
| `seed.py` | Creates tables and sample data |
| `routers/auth.py` | Register, login, "who am I" |
| `routers/products.py` | Catalog, product detail, create / edit / delete listings and photos |
| `routers/artisans.py` | Public artisan list and profiles (approved only) |
| `routers/ai.py` | AI status and the listing-assist endpoint |
| `routers/orders.py` | Place orders, list orders, artisan updates status + courier + tracking |
| `routers/admin.py` | Approve / reject artisans, basic stats |
| `routers/planned.py` | Feature status list and the "not implemented" stubs |

### Frontend (`frontend/src/`)

| File | Explanation |
|---|---|
| `main.jsx`, `App.jsx` | Starts React and defines which page shows at which URL |
| `api.js` | The only file that talks to the backend; every endpoint is a function here |
| `i18n.jsx` | English and Hindi labels, `t("key")` function, remembers the choice |
| `hooks.js`, `utils.js` | A small data-loading helper and formatting helpers |
| `context/AuthContext.jsx` | Remembers who is logged in |
| `context/CartContext.jsx` | Remembers the cart (in the browser) |
| `components/` | Reusable pieces: navbar, product card, loading / empty / error boxes, tags, route guard, language popup |
| `pages/` | One file per screen (home, shop, product, artisans, login, cart, checkout, orders, seller dashboard, listing form, admin, features, policies) |
| `styles.css` | All styling; responsive for phones and desktops |

---

## 7. API endpoint summary

All paths start with `/api`. "Auth" = needs `Authorization: Bearer <token>`.

| Method + path | Who | Purpose |
|---|---|---|
| `POST /auth/register` | public | Create buyer or artisan (artisans start as *pending*) |
| `POST /auth/login` | public | Returns `access_token` and `user` |
| `GET /auth/me` | any logged in | Current user |
| `GET /products` | public | Query: `q, category, min_price, max_price, artisan_id, sort, limit, offset` |
| `GET /products/categories` | public | Category list |
| `GET /products/mine` | artisan | Own listings |
| `GET /products/{id}` | public* | Detail (*owner/admin can see unapproved) |
| `GET /products/{id}/similar` | public | Demo-only same-category list |
| `POST /products` | approved artisan | Multipart: `title, description, category, price, stock, shipping_fee, ai_assisted, images[]` |
| `PUT /products/{id}` | owner | Same fields; `images[]` adds new photos |
| `DELETE /products/{id}/images/{image_id}` | owner | Remove one photo (keeps at least 1) |
| `DELETE /products/{id}` | owner or admin | Delete listing |
| `GET /artisans`, `GET /artisans/{id}` | public | Verified artisans only |
| `GET /ai/status` | public | `demo` or `live` mode |
| `POST /ai/listing-assist` | approved artisan | Multipart: `image`, `notes`. Returns suggestions only |
| `POST /orders` | buyer | `items[{product_id, quantity}]`, address fields, `simulate_payment` = `success` or `fail` |
| `GET /orders`, `GET /orders/{id}` | logged in | Buyer: own. Artisan: orders with their items. Admin: all |
| `PATCH /orders/items/{item_id}` | owning artisan | `status` (`packed/shipped/delivered`), `courier_name`, `tracking_id` |
| `GET /admin/stats` | admin | Basic counts |
| `GET /admin/artisans?status=pending` | admin | `pending / approved / rejected / all` |
| `POST /admin/artisans/{user_id}/approve` | admin | Gives Verified badge |
| `POST /admin/artisans/{user_id}/reject` | admin | Body: `reason` |
| `GET /features` | public | Status of every feature |
| `GET /planned/*` | public | Always `501` (not built yet) |

Errors always look like `{"detail": "readable message"}` (or a list for form validation problems);
the frontend turns both into friendly text.

---

## 8. Safety notes and known limits

- Prices and stock are re-checked **on the server** at checkout. The browser cart is only an estimate.
- Ownership is enforced on the server: an artisan cannot edit another artisan's listing or order items.
- Uploads: JPG/PNG/WEBP only, checked by file signature, max 5 MB, random names.
- Passwords are salted PBKDF2 hashes. The token secret comes from `.env`.
- Not included (needed before real use): rate limiting, email verification, password reset, HTTPS, database migrations (Alembic), automated tests, image virus scanning, real legal policies.
- Shipping is charged **once per product line**, not per unit. Prices are whole rupees.

### Moving to PostgreSQL later

Install a driver (`pip install "psycopg[binary]"`), create a database, and change one line in `.env`:
`DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/digi_karigari`. Then run `python -m app.seed --reset`.
For real projects add Alembic migrations instead of `create_all`.

---

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| Page says "Cannot reach the server" | Backend is not running. Start it (Window 1) and check http://127.0.0.1:8000/api/health |
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again |
| `py` is not recognised | Reinstall Python from python.org and tick "Add to PATH", or use `python` instead of `py` |
| `ModuleNotFoundError: No module named 'app'` | Run commands from inside the `backend` folder |
| `Address already in use` (port 8000 or 5173) | Close the old window, or use `--port 8001` and set `VITE_BACKEND_ORIGIN` / update `vite.config.js` |
| Login says incorrect email or password | Run `python -m app.seed --reset`; demo password is `demo1234` |
| Images do not show | Make sure the backend is running; seed images are created by the seed script |
| Language popup does not appear again | It is remembered. Clear site data for localhost, or use the language button in the menu |
| AI says "DEMO MODE" | Expected until `AI_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` are set in `backend/.env` (restart the backend after editing) |
| AI error 502 | Check the key and model name; you can always fill the form by hand |
| `npm install` fails | Check internet, Node 18+, and try deleting `node_modules` and running again |
| Want a clean start | Stop the backend, delete `backend/digi_karigari.db`, run `python -m app.seed --reset` |
