#Pytest configuration and fixtures for Django testing.
#Provides common fixtures and test setup for the entire test suite.
import pytest
import django
from django.test import Client
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.conf import settings
import json

if not settings.configured:
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def client():
    """
    Provides a Django test client for making HTTP requests.
    """
    return Client()


@pytest.fixture
def authenticated_client():
    """
    Provides a Django test client with an authenticated user session.
    """
    client = Client()
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    client.force_login(user)
    return client


@pytest.fixture
def test_user():
    """
    Creates a test user for use in tests.
    """
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user():
    """
    Creates an admin user for use in tests.
    """
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def request_factory():
    """
    Provides Django's RequestFactory for creating mock requests.
    """
    return RequestFactory()


@pytest.fixture
def mock_request(request_factory):
    """
    Creates a mock GET request with session middleware.
    """
    request = request_factory.get('/')
    # Add session middleware
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.fixture
def mock_post_request(request_factory):
    """
    Creates a mock POST request with session middleware and JSON data.
    """
    def _make_request(data=None):
        if data is None:
            data = {"lat": 40.7128, "lon": -74.0060}
        request = request_factory.post(
            '/api/location/',
            data=json.dumps(data),
            content_type='application/json'
        )
        # Add session middleware
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(request)
        request.session.save()
        return request
    return _make_request


@pytest.fixture
def sample_coordinates():
    """
    Provides sample coordinate data for testing.
    """
    return {
        "valid": {"lat": 40.7128, "lon": -74.0060},  # NYC coordinates
        "invalid_lat": {"lat": "invalid", "lon": -74.0060},
        "invalid_lon": {"lat": 40.7128, "lon": "invalid"},
        "missing_lat": {"lon": -74.0060},
        "missing_lon": {"lat": 40.7128},
        "out_of_range_lat": {"lat": 200, "lon": -74.0060},
        "out_of_range_lon": {"lat": 40.7128, "lon": 300}
    }


@pytest.fixture
def client_with_session():
    """
    Provides a Django test client with pre-configured session data.
    """
    client = Client()
    # Create a session with test data
    session = client.session
    session['coords'] = {"lat": 40.7128, "lon": -74.0060}
    session.save()
    return client


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Enable database access for all tests by default.
    This fixture is automatically used for all tests.
    """
    pass


@pytest.fixture
def test_settings(settings):
    """
    Modify Django settings for testing.
    """
    settings.DEBUG = True
    settings.SECRET_KEY = 'test-secret-key-for-testing'
    settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
    return settings


@pytest.fixture
def mock_invalid_json_request(request_factory):
    """
    Creates a mock POST request with invalid JSON data.
    """
    request = request_factory.post(
        '/api/location/',
        data='invalid json',
        content_type='application/json'
    )
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.fixture(scope="session")
def django_db_setup():
    """
    Set up the test database.
    """
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
