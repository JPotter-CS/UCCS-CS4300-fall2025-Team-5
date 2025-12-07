"""Pytest configuration and fixtures for Django tests."""

import json
import os

import django
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client, RequestFactory


if not settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
    django.setup()

User = get_user_model()


@pytest.fixture
def client():
    """Provide a Django test client for making HTTP requests."""
    return Client()


@pytest.fixture
def authenticated_client():
    """Provide a Django test client with an authenticated user."""
    client_obj = Client()
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )
    client_obj.force_login(user)
    return client_obj


@pytest.fixture
def test_user():
    """Create a standard test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def admin_user():
    """Create an admin (superuser) for tests."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
    )


@pytest.fixture
def request_factory():
    """Provide Django's RequestFactory for creating mock requests."""
    return RequestFactory()


@pytest.fixture
def mock_request(request_factory):
    """Create a mock GET request with session middleware."""
    request = request_factory.get("/")
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.fixture
def mock_post_request(request_factory):
    """Create a factory for POST requests with session + JSON data."""

    def _make_request(data=None):
        payload = data or {"lat": 40.7128, "lon": -74.0060}
        request = request_factory.post(
            "/api/location/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(request)
        request.session.save()
        return request

    return _make_request


@pytest.fixture
def sample_coordinates():
    """Provide sample coordinate data for testing."""
    return {
        "valid": {"lat": 40.7128, "lon": -74.0060},
        "invalid_lat": {"lat": "invalid", "lon": -74.0060},
        "invalid_lon": {"lat": 40.7128, "lon": "invalid"},
        "missing_lat": {"lon": -74.0060},
        "missing_lon": {"lat": 40.7128},
        "out_of_range_lat": {"lat": 200, "lon": -74.0060},
        "out_of_range_lon": {"lat": 40.7128, "lon": 300},
    }


@pytest.fixture
def client_with_session():
    """Provide a Django client with preconfigured session data."""
    client_obj = Client()
    session = client_obj.session
    session["coords"] = {"lat": 40.7128, "lon": -74.0060}
    session.save()
    return client_obj


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests by default."""
    # Just requesting the 'db' fixture is enough.
    yield


@pytest.fixture
def test_settings(settings):
    """Modify Django settings for testing."""
    settings.DEBUG = True
    settings.SECRET_KEY = "test-secret-key-for-testing"
    settings.ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
    return settings


@pytest.fixture
def mock_invalid_json_request(request_factory):
    """Create a mock POST request with invalid JSON data."""
    request = request_factory.post(
        "/api/location/",
        data="invalid json",
        content_type="application/json",
    )
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.fixture(scope="session")
def django_db_setup():
    """Configure the test database."""
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": False,
    }
