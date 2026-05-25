# Deployment Plan: Fun with Art → Production

## Architecture Overview

```mermaid
flowchart LR
    subgraph Vercel[Vercel - Frontend]
        REACT[React SPA - index.html]
        HTML[20 Standalone HTML Pages]
        SHARED[shared.js]
        ASSETS[Static Assets]
    end

    subgraph Railway[Railway - Backend]
        DJANGO[Django REST API]
        ADMIN[Django Admin]
        PG[(PostgreSQL)]
    end

    subgraph Cloudinary[Cloudinary]
        IMAGES[Product + Blog Images]
    end

    Vercel -->|API Calls| Railway
    Railway -->|Read/Write| PG
    Railway -->|Upload/Read| Cloudinary
```

---

## Phase 1: Project Hygiene (Local)

### 1.1 — Root `.gitignore`
Create at `c:\Users\stuti\OneDrive\Desktop\FunWithArts\.gitignore`:
- `__pycache__/`, `*.pyc`, `*.pyo`
- `.venv/`, `venv/`
- `node_modules/`
- `db.sqlite3`
- `.env` (important — contains Razorpay secrets)
- `dist/`, `build/`
- `backend/media/` (will be in Cloudinary)
- `.vscode/`

### 1.2 — Remove `db.sqlite3` from tracking
If already committed, `git rm --cached backend/db.sqlite3`

### 1.3 — Verify `.env` is not committed
The current `.env` contains real Razorpay test keys — must NOT be in git.

---

## Phase 2: Backend — PostgreSQL Migration

### 2.1 — Install PostgreSQL adapter
Add to [`backend/requirements.txt`](backend/requirements.txt):
```
psycopg2-binary>=2.9,<3
dj-database-url>=2.2,<3
cloudinary>=1.41,<2
gunicorn>=22,<23
whitenoise>=6.7,<7
```

### 2.2 — Update [`backend/backend/settings.py`](backend/backend/settings.py)
Changes needed:

**Database config** (replace lines 92-97):
```python
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}
```

**Static files for production** (add after STATIC_ROOT line 135):
```python
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

**Middleware** (add after SecurityMiddleware line 59):
```python
'whitenoise.middleware.WhiteNoiseMiddleware',
```

**Cloudinary** (add at end of file):
```python
CLOUDINARY_URL = os.getenv('CLOUDINARY_URL', '')
if CLOUDINARY_URL:
    INSTALLED_APPS.append('cloudinary')
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
```

**CORS origins** (update lines 139-146 to read from env properly):
Already reads from `DJANGO_CORS_ALLOWED_ORIGINS` env var — works for production.

**Production security** (add after DEBUG check line 198):
```python
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

### 2.3 — Add `Procfile` 
Create [`backend/Procfile`](backend/Procfile):
```
web: gunicorn backend.wsgi --log-file -
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
```

### 2.4 — Add `runtime.txt`
Create [`backend/runtime.txt`](backend/runtime.txt):
```
python-3.11.9
```

### 2.5 — Add `railway.json`
Create [`backend/railway.json`](backend/railway.json):
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn backend.wsgi --log-file -",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

---

## Phase 3: Frontend — Vercel Preparation

### 3.1 — Fix `window.__UDAAN_API_BASE__` in ALL standalone HTML pages

**Problem:** Only `index.html` and `workshop-confirmation.html` set `window.__UDAAN_API_BASE__`. The fallback in `shared.js` is `http://127.0.0.1:8000/api` — this breaks in production.

**Solution:** Add this script before `<script src="shared.js">` in ALL 22 HTML files:
```html
<script>window.__UDAAN_API_BASE__ = 'https://YOUR-RAILWAY-APP.railway.app/api';</script>
```

**Files that need this (20 files missing it):**
- `about.html`, `account.html`, `addresses.html`, `cart.html`, `checkout.html`
- `collection.html`, `contact.html`, `forgot-password.html`, `legacy-index.html`
- `legal.html`, `login.html`, `order-history.html`, `orders.html`
- `product.html`, `reset-password.html`, `search.html`, `settings.html`
- `studio.html`, `success.html`, `support.html`, `wishlist.html`

**Better approach:** Use a Vite env variable and inject at build time. Create `funwithart-main/.env.production`:
```
VITE_API_URL=https://YOUR-RAILWAY-APP.railway.app/api
```

Then update `index.html` line 19 to use `%VITE_API_URL%` (Vite replaces env vars in HTML). For standalone HTML pages, we'll create a single JS snippet file.

### 3.2 — Create [`funwithart-main/public/api-config.js`](funwithart-main/public/api-config.js)
```js
// This file is NOT processed by Vite — it's served as-is.
// Replace YOUR_RAILWAY_URL after Railway deploys backend.
window.__UDAAN_API_BASE__ = 'https://YOUR-RAILWAY-APP.railway.app/api';
```

### 3.3 — Add api-config.js to ALL HTML pages
Before `<script src="shared.js">` in every standalone HTML file:
```html
<script src="/api-config.js"></script>
```

### 3.4 — Create [`funwithart-main/vercel.json`](funwithart-main/vercel.json)
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm install",
  "rewrites": [
    { "source": "/about", "destination": "/about.html" },
    { "source": "/account", "destination": "/account.html" },
    { "source": "/addresses", "destination": "/addresses.html" },
    { "source": "/cart", "destination": "/cart.html" },
    { "source": "/checkout", "destination": "/checkout.html" },
    { "source": "/collection", "destination": "/collection.html" },
    { "source": "/contact", "destination": "/contact.html" },
    { "source": "/forgot-password", "destination": "/forgot-password.html" },
    { "source": "/legal", "destination": "/legal.html" },
    { "source": "/login", "destination": "/login.html" },
    { "source": "/order-history", "destination": "/order-history.html" },
    { "source": "/orders", "destination": "/orders.html" },
    { "source": "/product", "destination": "/product.html" },
    { "source": "/reset-password", "destination": "/reset-password.html" },
    { "source": "/search", "destination": "/search.html" },
    { "source": "/settings", "destination": "/settings.html" },
    { "source": "/studio", "destination": "/studio.html" },
    { "source": "/success", "destination": "/success.html" },
    { "source": "/support", "destination": "/support.html" },
    { "source": "/wishlist", "destination": "/wishlist.html" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

### 3.5 — Update Vite config for production
The Vite dev proxy (lines 12-23 in `vite.config.js`) doesn't apply in production — that's fine. But we need to update `index.html` API base from `'/api'` to the env variable:

Change `index.html` line 19 from:
```html
window.__UDAAN_API_BASE__ = '/api';
```
To:
```html
window.__UDAAN_API_BASE__ = '%VITE_API_URL%';
```

---

## Phase 4: Cloudinary Media Setup

### 4.1 — Install packages
Already in requirements.txt from Phase 2.1:
- `cloudinary>=1.41`
- `django-cloudinary-storage` (add this too)

### 4.2 — Cloudinary account
1. Sign up at https://cloudinary.com (free tier: 25GB storage, 25GB bandwidth/month)
2. Get the "Cloudinary URL" from dashboard (looks like `cloudinary://API_KEY:API_SECRET@CLOUD_NAME`)
3. Add to Railway env vars as `CLOUDINARY_URL`

### 4.3 — Migrate existing media
After deploy, manually upload existing images from `backend/media/` to Cloudinary via their web dashboard, or keep them locally since they already exist.

---

## Phase 5: Railway Deployment (Backend)

### 5.1 — Push to GitHub
```bash
cd c:\Users\stuti\OneDrive\Desktop\FunWithArts
git init
git add .
git commit -m "Production deployment setup"
git remote add origin YOUR_REPO_URL
git push -u origin main
```

### 5.2 — Create Railway project
1. Go to https://railway.app
2. "New Project" → "Deploy from GitHub repo"
3. Select your repo
4. **Set Root Directory to `backend`**
5. Add PostgreSQL plugin (Railway → your project → "New" → "Database" → "PostgreSQL")
   - Railway auto-injects `DATABASE_URL` env var — `dj-database-url` reads it automatically

### 5.3 — Add Railway Environment Variables
| Variable | Value |
|----------|-------|
| `DJANGO_SECRET_KEY` | Generate new: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_ALLOWED_HOSTS` | `YOUR-APP.railway.app,.vercel.app` |
| `DJANGO_CORS_ALLOWED_ORIGINS` | `https://YOUR-VERCEL-APP.vercel.app` |
| `RAZORPAY_KEY_ID` | `rzp_test_StI82O7Jm3heNM` (test) or live key |
| `RAZORPAY_KEY_SECRET` | Your test/live secret |
| `FRONTEND_URL` | `https://YOUR-VERCEL-APP.vercel.app` |
| `CLOUDINARY_URL` | From Cloudinary dashboard |
| `EMAIL_HOST` | Your email provider (or leave blank for console) |
| `EMAIL_HOST_USER` | Your email provider (or leave blank) |
| `EMAIL_HOST_PASSWORD` | Your email provider (or leave blank) |
| `DEFAULT_FROM_EMAIL` | `Fun with Art <hello@funwithart.com>` |
| `GOOGLE_CLIENT_ID` | Your Google OAuth client ID |

### 5.4 — Create superuser on Railway
After first deploy:
```bash
railway run python manage.py createsuperuser
```

---

## Phase 6: Vercel Deployment (Frontend)

### 6.1 — Deploy
1. Go to https://vercel.com
2. Import your GitHub repo
3. **Set Root Directory to `funwithart-main`**
4. Framework preset: Vite
5. Build command: `npm run build`
6. Output directory: `dist`
7. Add env variable: `VITE_API_URL` = `https://YOUR-RAILWAY-APP.railway.app/api`

### 6.2 — Post-deploy verification
- Visit `https://YOUR-APP.vercel.app` → React home page loads
- Visit `https://YOUR-APP.vercel.app/studio` → Studio page loads
- Visit `https://YOUR-APP.vercel.app/cart` → Cart page loads
- Add to cart → calls Railway API successfully
- Checkout → Razorpay modal opens correctly

---

## Phase 7: Post-Deployment Cleanup

### 7.1 — Switch Razorpay to live mode
- Get live keys from Razorpay Dashboard
- Update Railway env vars: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`
- Update `shared.js` if Razorpay key is referenced client-side

### 7.2 — Set up a custom domain (optional)
- Buy domain (e.g., funwithart.com)
- Point to Vercel via DNS
- Update `FRONTEND_URL`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CORS_ALLOWED_ORIGINS`

### 7.3 — Enable email delivery
- Sign up for Resend / SendGrid / Mailgun
- Update Railway email env vars

---

## Summary: Files to Change

| # | File | Action |
|---|------|--------|
| 1 | `../.gitignore` | **Create** — ignore venv, node_modules, db.sqlite3, .env, __pycache__ |
| 2 | `backend/requirements.txt` | **Edit** — add psycopg2-binary, dj-database-url, cloudinary, django-cloudinary-storage, gunicorn, whitenoise |
| 3 | `backend/backend/settings.py` | **Edit** — dj-database-url, whitenoise, Cloudinary storage, production security |
| 4 | `backend/Procfile` | **Create** |
| 5 | `backend/runtime.txt` | **Create** |
| 6 | `backend/railway.json` | **Create** |
| 7 | `funwithart-main/public/api-config.js` | **Create** — production API base URL |
| 8 | `funwithart-main/vercel.json` | **Create** — routing rules |
| 9 | `funwithart-main/.env.production` | **Create** — VITE_API_URL |
| 10 | `funwithart-main/index.html` | **Edit** — use VITE_API_URL env var |
| 11 | 20 standalone HTML files | **Edit** — add `<script src="/api-config.js">` before shared.js |
| 12 | `funwithart-main/account.html` | **Edit** — already needs shared.js line fix |