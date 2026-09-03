# Campaign Save 500 — Investigation Notes (2026-09-03)

**STATUS: RESOLVED (2026-09-03)** — see "Actual bug" and "Resolution" sections below.

## Symptom
`POST /api/studio/campaigns/` on `api.somtammarket.com` returns HTTP 500.
Example: request ID `Ty7JYeiuT8udrnvX55So4g`, `2026-09-03T13:37:06.934Z`,
`totalDuration: 90ms`, `upstreamRqDuration: 84ms`, no `upstreamErrors` —
the app received and processed the request, then errored.

## What was ruled out
- **Payload shape**: the incoming JSON (`title`, `overview`, `pillar`,
  `language`, `goal`, `keywords`, `posts[]`) matches `CampaignSerializer` /
  `CampaignPostSerializer` field-for-field. Not a validation shape mismatch.
- **Model/migration drift**: `CampaignPost.pillar` is a nullable FK
  (`null=True, blank=True`), so a missing per-post `pillar` isn't fatal.
  `python manage.py makemigrations --check --dry-run` → **"No changes
  detected"** — models and migrations are in sync locally.
- **Database connectivity**: confirmed with the user — the production
  Postgres (in the `precious-intuition` Railway project) is already
  provisioned and working. The DB is **not** the root cause.
- **Wrong Railway project confusion**: Railway's own assistant reported
  "only a Postgres database in the environment" — that was because it was
  looking at the *other* Railway project, `daring-grace`, which contains
  nothing but a leftover/unused standalone Postgres service. The real app
  lives in project `precious-intuition` → service `stm-food-backend`
  (service ID `53ed20c5-8588-4eed-9b82-d6e2e100c240`, production
  environment `11f22d30-d1d3-47e2-867f-72b20800f67a`). **Do not provision a
  new Postgres in `daring-grace`** — the working DB already lives in
  `precious-intuition`.

## Root cause found: production error logging is a black hole
`stm_food_backend/settings.py` has:
- `DEBUG = ENVIRONMENT != "production"` → `DEBUG=False` in prod
- **No custom `LOGGING` dict**
- **No `ADMINS` setting**

Django's *default* logging config (when no custom `LOGGING` is defined):
- Routes `django.request` (unhandled 500s) only to `mail_admins`, gated by
  a filter requiring `DEBUG=False`
- Gates the console handler the *opposite* way — it only prints when
  `DEBUG=True`

Net effect: in production, an unhandled exception producing a 500
**disappears completely** — no console/stdout output (so nothing reaches
Railway logs), and no admin email (since `ADMINS` is unset). Only explicit
`print()` calls (like the `📦 Incoming data` / `📷 Incoming FILES` lines in
`studio/views.py::CampaignViewSet.create`) show up in Railway logs, because
`print()` bypasses logging entirely.

This is why every attempt to find the actual traceback for this 500 came
up empty — pulling `deploy` logs for the exact timestamp window only ever
shows the two `print()` lines and nothing after.

## Actual bug: found via the new logging (commit 4cfec21)
Once `LOGGING` was deployed, the very next campaign-save attempt produced
a full traceback in Railway `deploy` logs:

```
File "/app/studio/views.py", line 38, in perform_create
    raise permissions.PermissionDenied("Not authorized to create campaigns")
AttributeError: module 'rest_framework.permissions' has no attribute 'PermissionDenied'
```

`rest_framework.permissions` has no `PermissionDenied` class — it lives in
`rest_framework.exceptions`. `CampaignViewSet.perform_create` (and
`perform_update`, same bug) used the wrong module, so the intended-403
authorization check crashed with a 500 instead every time it fired.

Checked `is_partner` for the test account (`farmer_kitchen@somtammarket.com`)
via `railway run` against prod — already `True`, so no account data needed
fixing, just the code.

## Resolution
1. `4cfec21` — added `LOGGING` config (stdout handler for `django.request` /
   root logger) so unhandled 500s stop vanishing in production.
2. `411fb2f` — `studio/views.py`: import `PermissionDenied` from
   `rest_framework.exceptions` and use it in both `perform_create` and
   `perform_update` instead of the nonexistent `permissions.PermissionDenied`.

Both deployed to `precious-intuition` → `stm-food-backend` (production).
User confirmed campaign save now succeeds, no more 500.

## Also done this session (unrelated cleanup)
Removed two dead files not imported anywhere in the codebase
(`studio/views.py` imports `gen_auto_post, gen_review_reply, gen_campaign`
from `.ai`, not `.ai_new`):
- `studio/ai_new.py`
- `studio/ai_original.py`
Committed as `d69f9dd`.

## Proposed next step (not yet applied — pending user go-ahead)
Add a `LOGGING` config to `stm_food_backend/settings.py` so unhandled
exceptions print to stdout (captured by Railway). Scoped strictly to
logging output — does not touch `AUTH_USER_MODEL`, JWT/auth middleware, or
any view/serializer/model logic in `studio`, `thefood`, or `orders`. A
request that succeeds today still succeeds identically; a request that
already 500s still 500s, just with a visible traceback next time.

User wants to move carefully here specifically because `thefood` shares
the same auth system as `studio` — noted for context, but the proposed
logging change does not touch auth code.
