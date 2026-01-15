
# [Django :Current Project folder] 

# Task: Create a full read-only API endpoint for the Category model using Django Rest Framework (DRF).

1. Context: These categories are central to the app's search and discovery feature. 
2. Serializer (thefood/serializers.py): > - Create CategorySerializer including id, name, slug, icon, and image. 
3. ViewSet (thefood/views.py): > - Use ReadOnlyModelViewSet.

#Crucial: Set lookup_field = 'slug' so the frontend can retrieve categories by their slug. 
4. URLs: > - In thefood/urls.py, use DefaultRouter to register the viewset.

#In the main urls.py, include these under the api/ path.

#Stop after generating the code for these three files.

# update the `PartnerStore` model to include a `StoreLocation` :

**"In the Django file `thefood/models.py`, update the `PartnerStore` model to include a `StoreLocation` 
(field or foreign key) and establish a relationship that links it to `Product` models to enable location-based search features."**


# Skill Task: Fix Django Admin Login in Railway Production (STM Food backend)

## Problem
On production (Railway), Django admin login page loads at:
`https://stm-food-backend-production.up.railway.app/admin/login/?next=/admin/`
…but login fails.

Database is intact (users exist). This is NOT a 404 routing issue anymore.
Goal: make admin login work reliably in production.

## Constraints
- Do NOT delete users or reset database.
- Make minimal safe changes.
- Keep existing API auth behavior working (JWT/cookie auth etc.).
- All changes must be committed and deployable on Railway.

## Diagnose first (must)
1. Reproduce locally with production-like settings if possible OR reason based on settings.
2. Determine which failure mode applies:
   A) “Please enter the correct username and password for a staff account.”
   B) CSRF verification failed (403)
   C) Redirect loop / cookie not set / immediate bounce back to login
   D) “This account is inactive”
   E) Silent failure due to custom auth backend mismatch

## Fix checklist (implement what applies)

### 1) Ensure admin authentication backend works (very common)
In `settings.py`, ensure default Django backend is included:
```py
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    # keep custom backend(s) below if used for API

TASK: Fix the '403 Forbidden' error encountered when trying to log in to the Django Admin interface in production.

CONTEXT:
*   Project: STM Marketplace (Django Backend).
*   Admin URL with Error: https://stm-food-backend-production.up.railway.app/admin/login/?next=/admin/
*   Environment: Django deployed on Railway. The 403 error is typically a security misconfiguration on the backend when deployed.

INSTRUCTION:
Generate the Python code required to safely update the `settings.py` file to allow access to the Django Admin at the specified production URL.

ACTION REQUIRED:
1.  Update the **ALLOWED_HOSTS** setting to include the production domain name.
2.  Update the **CSRF_TRUSTED_ORIGINS** setting to include the production host's protocol and domain to allow POST requests (like the login form) from the expected origin.

Expected Output: A Python snippet showing the suggested values for `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in `settings.py`.

