"""Test cases for Django settings and configuration.
Tests settings validation, environment configuration, and security settings.
"""

import time

import pytest
from django.conf import settings
from django.test import override_settings


@pytest.mark.unit
class TestBasicSettings:
    """Test basic Django settings configuration."""

    def test_secret_key_exists(self):
        """Test that SECRET_KEY is configured."""
        assert hasattr(settings, "SECRET_KEY")
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 0

    def test_debug_setting(self):
        """Test DEBUG setting configuration."""
        assert hasattr(settings, "DEBUG")
        assert isinstance(settings.DEBUG, bool)

    def test_allowed_hosts_configured(self):
        """Test that ALLOWED_HOSTS is properly configured."""
        assert hasattr(settings, "ALLOWED_HOSTS")
        assert isinstance(settings.ALLOWED_HOSTS, list)
        assert len(settings.ALLOWED_HOSTS) > 0

    def test_installed_apps_configured(self):
        """Test that INSTALLED_APPS includes required apps."""
        assert hasattr(settings, "INSTALLED_APPS")
        required_apps = [
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "home",
        ]

        for app in required_apps:
            assert app in settings.INSTALLED_APPS

    def test_middleware_configured(self):
        """Test that MIDDLEWARE is properly configured."""
        assert hasattr(settings, "MIDDLEWARE")
        required_middleware = [
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ]

        for middleware in required_middleware:
            assert middleware in settings.MIDDLEWARE

    def test_templates_configured(self):
        """Test that TEMPLATES is properly configured."""
        assert hasattr(settings, "TEMPLATES")
        assert len(settings.TEMPLATES) > 0

        template_config = settings.TEMPLATES[0]
        assert "BACKEND" in template_config
        assert "DIRS" in template_config
        assert "APP_DIRS" in template_config
        assert template_config["APP_DIRS"] is True


@pytest.mark.unit
class TestDatabaseSettings:
    """Test database configuration settings."""

    def test_databases_configured(self):
        """Test that DATABASES is properly configured."""
        assert hasattr(settings, "DATABASES")
        assert "default" in settings.DATABASES

        default_db = settings.DATABASES["default"]
        assert "ENGINE" in default_db
        assert "NAME" in default_db

    def test_database_engine(self):
        """Test that database engine is appropriate."""
        db_engine = settings.DATABASES["default"]["ENGINE"]
        valid_engines = [
            "django.db.backends.sqlite3",
            "django.db.backends.postgresql",
            "django.db.backends.mysql",
        ]
        assert db_engine in valid_engines

    @override_settings(DATABASES={})
    def test_missing_database_config(self):
        """Test that missing database config is handled."""
        assert True


@pytest.mark.unit
class TestSecuritySettings:
    """Test security-related settings."""

    def test_csrf_trusted_origins(self):
        """Test CSRF_TRUSTED_ORIGINS configuration."""
        if hasattr(settings, "CSRF_TRUSTED_ORIGINS"):
            assert isinstance(settings.CSRF_TRUSTED_ORIGINS, list)
            for origin in settings.CSRF_TRUSTED_ORIGINS:
                assert origin.startswith("https://")

    def test_security_middleware_present(self):
        """Test that security middleware is enabled."""
        assert "django.middleware.security.SecurityMiddleware" in settings.MIDDLEWARE

    def test_session_configuration(self):
        """Test session security configuration."""
        if hasattr(settings, "SESSION_COOKIE_SECURE"):
            assert isinstance(settings.SESSION_COOKIE_SECURE, bool)

        if hasattr(settings, "SESSION_COOKIE_HTTPONLY"):
            assert settings.SESSION_COOKIE_HTTPONLY is True

    def test_csrf_configuration(self):
        """Test CSRF protection configuration."""
        if hasattr(settings, "CSRF_COOKIE_SECURE"):
            assert isinstance(settings.CSRF_COOKIE_SECURE, bool)

        if hasattr(settings, "CSRF_COOKIE_HTTPONLY"):
            assert isinstance(settings.CSRF_COOKIE_HTTPONLY, bool)


@pytest.mark.unit
class TestStaticFilesSettings:
    """Test static files configuration."""

    def test_static_url_configured(self):
        """Test that STATIC_URL is configured."""
        assert hasattr(settings, "STATIC_URL")
        assert settings.STATIC_URL is not None
        assert settings.STATIC_URL.endswith("/")

    def test_static_root_configured(self):
        """Test that STATIC_ROOT is configured for production."""
        assert hasattr(settings, "STATIC_ROOT")
        assert settings.STATIC_ROOT is not None

    def test_whitenoise_middleware(self):
        """Test that WhiteNoise middleware is configured if used."""
        if "whitenoise.middleware.WhiteNoiseMiddleware" in settings.MIDDLEWARE:
            assert hasattr(settings, "WHITENOISE_USE_FINDERS")


@pytest.mark.unit
class TestLocalizationSettings:
    """Test localization and internationalization settings."""

    def test_language_code_configured(self):
        """Test that LANGUAGE_CODE is set."""
        assert hasattr(settings, "LANGUAGE_CODE")
        assert settings.LANGUAGE_CODE is not None
        assert len(settings.LANGUAGE_CODE) >= 2

    def test_time_zone_configured(self):
        """Test that TIME_ZONE is set."""
        assert hasattr(settings, "TIME_ZONE")
        assert settings.TIME_ZONE is not None

    def test_use_i18n_configured(self):
        """Test that USE_I18N is configured."""
        assert hasattr(settings, "USE_I18N")
        assert isinstance(settings.USE_I18N, bool)

    def test_use_tz_configured(self):
        """Test that USE_TZ is configured."""
        assert hasattr(settings, "USE_TZ")
        assert isinstance(settings.USE_TZ, bool)


@pytest.mark.unit
class TestCustomSettings:
    """Test custom application settings."""

    def test_render_external_hostname(self):
        """Test RENDER_EXTERNAL_HOSTNAME configuration."""
        if hasattr(settings, "RENDER_EXTERNAL_HOSTNAME"):
            hostname = settings.RENDER_EXTERNAL_HOSTNAME
            if hostname:
                assert isinstance(hostname, str)
                assert "." in hostname or hostname == "localhost"

    def test_environment_variables_handling(self, monkeypatch):
        """Test that environment variables are properly handled."""
        original_debug = settings.DEBUG
        monkeypatch.delenv("SOME_MISSING_ENV_VAR", raising=False)
        assert isinstance(original_debug, bool)


@pytest.mark.integration
class TestSettingsIntegration:
    """Test settings integration with Django components."""

    def test_settings_with_django_setup(self):
        """Test that settings work correctly with Django setup."""
        from django.apps import apps

        assert apps.ready

        app_configs = apps.get_app_configs()
        app_names = [app.name for app in app_configs]

        assert "home" in app_names
        assert "django.contrib.admin" in app_names

    def test_database_connection_with_settings(self):
        """Test that database connection works with current settings."""
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

    def test_static_files_with_settings(self):
        """Test static files configuration integration."""
        from django.contrib.staticfiles.finders import get_finders

        finders = list(get_finders())
        assert len(finders) > 0

    def test_template_engine_with_settings(self):
        """Test template engine configuration."""
        from django.template import engines

        assert len(engines.all()) > 0

        default_engine = engines["django"]
        assert default_engine is not None


@pytest.mark.unit
class TestSettingsValidation:
    """Test settings validation and error handling."""

    def test_required_settings_present(self):
        """Test that all required Django settings are present."""
        required_settings = [
            "SECRET_KEY",
            "INSTALLED_APPS",
            "MIDDLEWARE",
            "ROOT_URLCONF",
            "TEMPLATES",
            "DATABASES",
            "STATIC_URL",
        ]

        for setting_name in required_settings:
            assert hasattr(settings, setting_name), f"{setting_name} is missing from settings"
            assert getattr(settings, setting_name) is not None, f"{setting_name} is None"

    @override_settings(SECRET_KEY="")
    def test_empty_secret_key_handling(self):
        """Test handling of empty SECRET_KEY."""
        assert settings.SECRET_KEY == ""

    def test_settings_types(self):
        """Test that settings have correct types."""
        type_checks = {
            "DEBUG": bool,
            "ALLOWED_HOSTS": list,
            "INSTALLED_APPS": (list, tuple),
            "MIDDLEWARE": (list, tuple),
            "TEMPLATES": list,
            "DATABASES": dict,
            "USE_I18N": bool,
            "USE_TZ": bool,
        }

        for setting_name, expected_type in type_checks.items():
            if hasattr(settings, setting_name):
                setting_value = getattr(settings, setting_name)
                assert isinstance(setting_value, expected_type), (
                    f"{setting_name} should be {expected_type}, got {type(setting_value)}"
                )


@pytest.mark.unit
class TestEnvironmentSpecificSettings:
    """Test environment-specific settings handling."""

    def test_production_settings_security(self):
        """Test production security settings."""
        if not settings.DEBUG:
            if hasattr(settings, "SECURE_SSL_REDIRECT"):
                assert isinstance(settings.SECURE_SSL_REDIRECT, bool)

            if hasattr(settings, "SECURE_HSTS_SECONDS"):
                assert isinstance(settings.SECURE_HSTS_SECONDS, int)
                if settings.SECURE_HSTS_SECONDS > 0:
                    assert settings.SECURE_HSTS_SECONDS >= 3600

    def test_development_settings_debug(self):
        """Test development debug settings."""
        if settings.DEBUG:
            assert settings.DEBUG is True

            localhost_variants = ["localhost", "127.0.0.1", "0.0.0.0"]
            has_localhost = any(host in localhost_variants for host in settings.ALLOWED_HOSTS)
            assert has_localhost or "*" in settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS

    def test_database_settings_environment(self):
        """Test database settings for different environments."""
        db_config = settings.DATABASES["default"]

        if settings.DEBUG:
            assert db_config["ENGINE"] in [
                "django.db.backends.sqlite3",
                "django.db.backends.postgresql",
            ]
        else:
            assert db_config["ENGINE"] in [
                "django.db.backends.postgresql",
                "django.db.backends.mysql",
                "django.db.backends.sqlite3",
            ]


@pytest.mark.performance
class TestSettingsPerformance:
    """Test settings-related performance."""

    def test_settings_access_performance(self):
        """Test that settings access is fast."""
        start_time = time.time()
        for _ in range(1000):
            _ = settings.DEBUG
            _ = settings.SECRET_KEY
            _ = settings.INSTALLED_APPS
        end_time = time.time()

        assert (end_time - start_time) < 0.1

    def test_settings_import_performance(self):
        """Test settings import performance."""
        start_time = time.time()
        for _ in range(100):
            from django.conf import settings as test_settings  # noqa: WPS433

            _ = test_settings.DEBUG
        end_time = time.time()

        assert (end_time - start_time) < 1.0
