from django.test import TestCase
from django.conf import settings


class SettingsTests(TestCase):
    def test_modelbackend_in_auth_backends(self):
        """Ensure default ModelBackend is present so admin/session login works."""
        self.assertIn('django.contrib.auth.backends.ModelBackend', settings.AUTHENTICATION_BACKENDS)

    def test_cookie_domain_not_forced_by_default(self):
        """CSRF/SESSION cookie domain should not be forced to .somtammarket.com by default."""
        self.assertTrue(getattr(settings, 'CSRF_COOKIE_DOMAIN', None) in (None, ''),
                        f"CSRF_COOKIE_DOMAIN was set to {settings.CSRF_COOKIE_DOMAIN}")

    def test_railway_domain_is_trusted_in_production(self):
        """If running with ENVIRONMENT=production, ensure Railway backend domain is trusted for CSRF."""
        if settings.ENVIRONMENT == 'production':
            self.assertIn('https://stm-food-backend-production.up.railway.app', settings.CSRF_TRUSTED_ORIGINS)
        else:
            self.skipTest('Not running with ENVIRONMENT=production; skipping')
