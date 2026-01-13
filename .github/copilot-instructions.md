# Copilot / AI Agent Instructions for Somtam Market Backend

Purpose: Give concise, actionable context so an AI coding agent can be immediately productive in this repo.

Quick facts
- Tech stack: Django 4.2 backend, Django REST Framework, PostgreSQL (defaults to Railway), JWT auth via djangorestframework_simplejwt, OpenAI integration via `studio/ai.py` (uses `OPENAI_API_KEY`).
- Virtualenv present at `foodvenv/` (Windows: `foodvenv\Scripts\activate` or `Activate.ps1`).
- Use `.env` in project root for secrets (`DJANGO_SECRET_KEY`, `OPENAI_API_KEY`, `POSTGRES_*`).

Where to start (high-value files)
- `manage.py` — project entrypoint for dev commands: runserver, migrate, test.
- `stm_food_backend/settings.py` — environment flags, CORS/CSRF, DB defaults, and important globals.
- `stm_food_backend/urls.py` — mounts: `/admin/`, JWT endpoints (`/api/token/`, `/api/token/refresh/`), and `api/me/` profile endpoint.
- `thefood/` — main app: models for `User`, `Product`, `Order`, `Recipe`, `Blog` (see `thefood/models.py`); API routes in `thefood/urls.py` (Products ViewSet, order endpoints).
- `studio/ai.py` — OpenAI usage; `gen_campaign`, `gen_auto_post`, `gen_review_reply` with graceful fallbacks.

Important architectural & code conventions
- Custom User model: `thefood.User` uses `email` as `USERNAME_FIELD` and a `CustomUserManager`. Create/identify users by `email`.
- Image handling: Image fields are stored as URLs (e.g., `Product.image`, `Category.image`, `PartnerStore.logo`, `UserProfile.avatar` use `URLField`). Code often expects external (hosted) images rather than Django `ImageField` uploads.
- Slugs: `Product.slug` is auto-generated in `Product.save()` to be unique (appends `-2`/`-3` if needed). Use slugs when linking products.
- API authentication: JWT tokens via `/api/token/` (`TokenObtainPairView`) and `/api/token/refresh/`. `MyProfileView` is protected with `IsAuthenticated`.
- OpenAI integration: `studio.ai.get_client()` reads `OPENAI_API_KEY` from env; generation functions expect/return JSON and use `gpt-4o-mini`.

Developer workflows & commands
- Start dev: activate virtualenv, install deps, run server:
  - Windows (PowerShell): `.\foodvenv\Scripts\Activate.ps1` then `pip install -r requirements.txt`
  - Run migrations: `python manage.py migrate`
  - Create admin: `python manage.py createsuperuser` (email is required)
  - Run dev server: `python manage.py runserver`
- Tests: run `python manage.py test`. (There are currently placeholder/empty tests; add tests alongside changes.)
- Static & media: `STATIC_ROOT` = `staticfiles/`, `MEDIA_ROOT` = `media/`. In DEBUG Django serves media files according to `settings.py` while running dev server.

Notable integration points & deployment notes
- DB: production assumes PostgreSQL; connection pulls from `POSTGRES_DB/USER/PASSWORD/HOST/PORT` env vars (defaults are Railway values). Be careful when testing locally (a checkout includes `db.sqlite3`).
- CORS/CSRF: `settings.py` lists allowed origins (Vercel, somtammarket.com, local dev). API is built to serve a separate frontend (hosted on Vercel / somtammarket).
- OpenAI: `studio/ai.py` uses the official `openai` client and handles quota/exception fallbacks — ensure `OPENAI_API_KEY` available for running related features.

Project-specific gotchas & helpful tips
- `UserProfile.avatar` is a `URLField`. `stm_food_backend.views.MyProfileView` calls `profile.avatar.url` — this can raise if `avatar` is a plain URL string (no `.url` attribute). Be cautious when changing avatar handling.
- Images are URLs, not stored files. When adding features that upload images, prefer adding new `ImageField` + storage backed logic rather than switching existing URL fields globally.
- The project uses JWT + `IsAuthenticated` for protected endpoints; tests or live calls should obtain tokens via `/api/token/` and send `Authorization: Bearer <token>`.

How to make safe changes (suggestions for AI agents)
- Run migrations locally when changing models (`makemigrations` then `migrate`).
- Add focused tests for each model/endpoint change; examples live in `thefood/tests.py`, `studio/tests.py`, `orders/tests.py` (replace placeholders).
- When modifying settings, prefer feature flags via env vars (already used via `ENVIRONMENT`/`.env`).

If you need an example task to get started
- Add unit tests for `Product.slug` uniqueness (create duplicate titles and assert unique slugs are generated).
- Add a small test for `studio.gen_campaign` fallback JSON when `OPENAI_API_KEY` is missing.

If anything here seems incomplete or you want extra detail (API examples, more file references, or a checklist for PRs), tell me which area to expand and I will iterate. ✅
