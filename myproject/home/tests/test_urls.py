"""Test cases for URL patterns and routing in the Django project."""
import json
import time
import pytest
from django.urls import reverse, resolve


@pytest.mark.unit
class TestURLPatterns:
    """Test URL pattern resolution and reverse lookup."""

    def test_index_url_resolves(self):
        """Test that root URL resolves to index view."""
        resolver = resolve("/")
        assert resolver.view_name == "index"
        assert resolver.func.__name__ == "index"

    def test_location_page_url_resolves(self):
        """Test that location URL resolves to location_page view."""
        resolver = resolve("/location/")
        assert resolver.view_name == "location_page"
        assert resolver.func.__name__ == "location_page"

    def test_save_location_api_url_resolves(self):
        """Test that API location URL resolves to save_location view."""
        resolver = resolve("/api/location/")
        assert resolver.view_name == "save_location"
        assert resolver.func.__name__ == "save_location"

    def test_index_url_reverse_lookup(self):
        """Test reverse lookup for index URL."""
        url = reverse("index")
        assert url == "/"

    def test_location_page_url_reverse_lookup(self):
        """Test reverse lookup for location page URL."""
        url = reverse("location_page")
        assert url == "/location/"

    def test_save_location_url_reverse_lookup(self):
        """Test reverse lookup for save location API URL."""
        url = reverse("save_location")
        assert url == "/api/location/"

    @pytest.mark.parametrize(
        "url_name,expected_path",
        [
            ("index", "/"),
            ("location_page", "/location/"),
            ("save_location", "/api/location/"),
        ],
    )
    def test_all_url_reverse_lookups(self, url_name, expected_path):
        """Test reverse lookup for all defined URLs."""
        url = reverse(url_name)
        assert url == expected_path


@pytest.mark.integration
class TestURLAccessibility:
    """Test that all URLs are accessible via HTTP requests."""

    def test_index_url_accessible(self, client):
        """Test that index URL is accessible."""
        response = client.get("/")
        assert response.status_code == 200

    def test_location_page_url_accessible(self, client):
        """Test that location page URL is accessible."""
        response = client.get("/location/")
        assert response.status_code == 200

    def test_save_location_api_url_accessible_post(self, client):
        """Test that save location API URL accepts POST requests."""
        response = client.post(
            "/api/location/",
            data=json.dumps({"lat": 40.7128, "lon": -74.0060}),
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_save_location_api_url_get_not_allowed(self, client):
        """Test that save location API URL rejects GET requests."""
        response = client.get("/api/location/")
        assert response.status_code == 405  # Method Not Allowed

    @pytest.mark.parametrize(
        "path",
        [
            "/",
            "/location/",
        ],
    )
    def test_get_requests_successful(self, client, path):
        """Test that GET requests to main pages are successful."""
        response = client.get(path)
        assert response.status_code == 200


@pytest.mark.unit
class TestURLNotFound:
    """Test handling of invalid/non-existent URLs."""

    def test_nonexistent_url_returns_404(self, client):
        """Test that non-existent URLs return 404."""
        response = client.get("/nonexistent-page/")
        assert response.status_code == 404

    def test_invalid_api_endpoint_returns_404(self, client):
        """Test that invalid API endpoints return 404."""
        response = client.get("/api/invalid/")
        assert response.status_code == 404

    @pytest.mark.parametrize(
        "invalid_path",
        [
            "/invalid/",
            "/api/invalid/",
            "/location/invalid/",
            "/static/nonexistent.css",
        ],
    )
    def test_various_invalid_urls(self, client, invalid_path):
        """Test various invalid URL patterns return 404."""
        response = client.get(invalid_path)
        assert response.status_code == 404


@pytest.mark.unit
class TestURLPatternSecurity:
    """Test URL pattern security considerations."""

    def test_trailing_slash_handling(self, client):
        """Test that URLs handle trailing slashes appropriately."""
        response = client.get("/location")
        assert response.status_code in [200, 301, 302]

        response = client.get("/location/")
        assert response.status_code == 200

    def test_api_url_trailing_slash(self, client):
        """Test API URL trailing slash handling."""
        # Test API with trailing slash
        response = client.post(
            "/api/location/",
            data=json.dumps({"lat": 40.7128, "lon": -74.0060}),
            content_type="application/json",
        )
        assert response.status_code == 200

        # Test API without trailing slash
        response = client.post(
            "/api/location",
            data=json.dumps({"lat": 40.7128, "lon": -74.0060}),
            content_type="application/json",
        )
        # Should either work (200) or redirect (301/302)
        assert response.status_code in [200, 301, 302, 404]

    def test_url_case_sensitivity(self, client):
        """Test that URLs are case sensitive as expected."""
        response = client.get("/location/")
        assert response.status_code == 200

        response = client.get("/Location/")
        assert response.status_code == 404

    def test_double_slash_handling(self, client):
        """Test handling of double slashes in URLs."""
        response = client.get("/location//")
        # Could be 404 or redirected, depends on server configuration
        assert response.status_code in [200, 301, 302, 404]


@pytest.mark.integration
class TestURLParameterHandling:
    """Test URL parameter handling and edge cases."""

    def test_query_parameters_ignored_for_routing(self, client):
        """Test that query parameters don't affect URL routing."""
        response = client.get("/?test=param")
        assert response.status_code == 200

        response = client.get("/location/?coords=test")
        assert response.status_code == 200

    def test_fragment_identifiers_ignored(self, client):
        """Test that fragment identifiers don't affect routing."""
        response = client.get("/")  # client never sends fragment to server
        assert response.status_code == 200


@pytest.mark.unit
class TestAdminURLs:
    """Test admin URL accessibility (if admin is enabled)."""

    def test_admin_url_exists(self, client):
        """Test that admin URL is accessible (might require login)."""
        response = client.get("/admin/")
        assert response.status_code in [200, 302]

    def test_admin_login_url_accessible(self, client):
        """Test that admin login URL is accessible."""
        response = client.get("/admin/login/")
        assert response.status_code == 200


@pytest.mark.performance
class TestURLPerformance:
    """Test URL resolution performance."""

    def test_url_resolution_performance(self):
        """Test that URL resolution is fast."""
        start_time = time.time()
        for _ in range(100):
            resolve("/")
            resolve("/location/")
            resolve("/api/location/")
        end_time = time.time()

        assert (end_time - start_time) < 0.1  # <100ms for 300 resolutions

    def test_reverse_lookup_performance(self):
        """Test that reverse URL lookup is fast."""
        start_time = time.time()
        for _ in range(100):
            reverse("index")
            reverse("location_page")
            reverse("save_location")
        end_time = time.time()

        assert (end_time - start_time) < 0.1  # <100ms for 300 lookups
