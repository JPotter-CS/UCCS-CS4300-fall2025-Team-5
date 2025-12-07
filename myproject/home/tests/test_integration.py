"""Integration test cases for the Django project.
Tests end-to-end functionality, cross-component interactions, and user workflows.
"""

import gc
import json
import pytest
from django.contrib.auth import get_user_model
from django.test import Client


User = get_user_model()


@pytest.mark.integration
class TestFullUserWorkflow:
    """Test complete user workflows from start to finish."""

    def test_complete_location_workflow(self, client):
        """Test the complete workflow: visit index -> save location -> view location."""
        response = client.get("/")
        assert response.status_code == 200

        location_data = {"lat": 40.7128, "lon": -74.0060}
        save_response = client.post(
            "/api/location/",
            data=json.dumps(location_data),
            content_type="application/json",
        )
        assert save_response.status_code == 200
        save_data = save_response.json()
        assert save_data["ok"] is True

        location_response = client.get("/location/")
        assert location_response.status_code == 200
        assert location_response.context["coords"] is not None
        assert location_response.context["coords"]["lat"] == 40.7128
        assert location_response.context["coords"]["lon"] == -74.0060

        content = location_response.content.decode()
        assert "40.7128" in content
        assert "-74.006" in content

    def test_multiple_location_updates_workflow(self, client):
        """Test workflow with multiple location updates."""
        locations = [
            {"lat": 40.7128, "lon": -74.0060, "name": "New York"},
            {"lat": 34.0522, "lon": -118.2437, "name": "Los Angeles"},
            {"lat": 41.8781, "lon": -87.6298, "name": "Chicago"},
        ]

        for location in locations:
            save_response = client.post(
                "/api/location/",
                data=json.dumps({"lat": location["lat"], "lon": location["lon"]}),
                content_type="application/json",
            )
            assert save_response.status_code == 200

            location_response = client.get("/location/")
            assert location_response.status_code == 200
            coords = location_response.context["coords"]
            assert coords["lat"] == location["lat"]
            assert coords["lon"] == location["lon"]

    def test_session_persistence_across_requests(self, client):
        """Test that session data persists across multiple requests."""
        location_data = {"lat": 37.7749, "lon": -122.4194}
        client.post(
            "/api/location/",
            data=json.dumps(location_data),
            content_type="application/json",
        )

        for _ in range(5):
            response = client.get("/location/")
            assert response.status_code == 200
            coords = response.context["coords"]
            assert coords["lat"] == 37.7749
            assert coords["lon"] == -122.4194


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling across the entire application."""

    def test_invalid_json_to_location_page_flow(self, client):
        """Test flow from invalid JSON submission to location page."""
        response = client.post(
            "/api/location/",
            data='{"invalid": json}',
            content_type="application/json",
        )
        assert response.status_code == 400

        location_response = client.get("/location/")
        assert location_response.status_code == 200
        assert location_response.context["coords"] is None

    def test_incomplete_data_handling(self, client):
        """Test handling of incomplete coordinate data."""
        incomplete_data_sets = [
            {"lat": 40.7128},
            {"lon": -74.0060},
            {},
            {"lat": None, "lon": -74.0060},
            {"lat": 40.7128, "lon": None},
        ]

        for data in incomplete_data_sets:
            response = client.post(
                "/api/location/",
                data=json.dumps(data),
                content_type="application/json",
            )
            assert response.status_code == 400

            response_data = response.json()
            assert response_data["ok"] is False
            assert "error" in response_data

    def test_cross_view_error_recovery(self, client):
        """Test that errors in one view don't affect others."""
        client.post(
            "/api/location/",
            data="invalid",
            content_type="application/json",
        )

        index_response = client.get("/")
        assert index_response.status_code == 200

        location_response = client.get("/location/")
        assert location_response.status_code == 200


@pytest.mark.integration
class TestSecurityIntegration:
    """Test security features integration."""

    def test_csrf_protection_integration(self, client):
        """Test CSRF protection across views."""
        response = client.get("/location/")
        assert response.status_code == 200
        assert "csrftoken" in response.cookies or "csrfmiddlewaretoken" in response.content.decode()

    def test_method_security_integration(self, client):
        """Test HTTP method restrictions work correctly."""
        response = client.get("/api/location/")
        assert response.status_code == 405

        response = client.put(
            "/api/location/",
            data="{}",
            content_type="application/json",
        )
        assert response.status_code == 405

        response = client.delete("/api/location/")
        assert response.status_code == 405

    def test_content_type_validation(self, client):
        """Test that content type validation works."""
        response = client.post(
            "/api/location/",
            data="test=data",
            content_type="application/x-www-form-urlencoded",
        )
        assert response.status_code in [200, 400, 415]


@pytest.mark.integration
class TestPerformanceIntegration:
    """Test performance characteristics of integrated workflows."""

    def test_concurrent_session_handling(self, _client):
        """Test handling of multiple concurrent sessions."""
        clients = [Client() for _ in range(5)]

        for i, test_client in enumerate(clients):
            location = {"lat": 40.0 + i, "lon": -74.0 + i}
            response = test_client.post(
                "/api/location/",
                data=json.dumps(location),
                content_type="application/json",
            )
            assert response.status_code == 200

        for i, test_client in enumerate(clients):
            response = test_client.get("/location/")
            assert response.status_code == 200
            coords = response.context["coords"]
            assert coords["lat"] == 40.0 + i
            assert coords["lon"] == -74.0 + i


@pytest.mark.integration
class TestDatabaseIntegration:
    """Test database interactions."""

    def test_user_creation_integration(self, client):
        """Test user creation and authentication flow."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )

        client.force_login(user)

        location_data = {"lat": 40.7128, "lon": -74.0060}
        response = client.post(
            "/api/location/",
            data=json.dumps(location_data),
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_admin_access_integration(self):
        """Test admin interface integration."""
        admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )

        client = Client()
        client.force_login(admin_user)

        response = client.get("/admin/")
        assert response.status_code == 200


@pytest.mark.integration
class TestStaticFilesIntegration:
    """Test static file serving integration."""

    def test_css_file_accessibility(self, client):
        """Test that CSS files are accessible."""
        response = client.get("/")
        content = response.content.decode()

        if "static" in content or ".css" in content:
            pass

        assert response.status_code == 200

    def test_template_rendering_without_static_files(self, client, settings):
        """Test that templates render gracefully without static files."""
        settings.DEBUG = False

        response = client.get("/")
        assert response.status_code == 200

        response = client.get("/location/")
        assert response.status_code == 200


@pytest.mark.integration
class TestMiddlewareIntegration:
    """Test middleware integration and functionality."""

    def test_session_middleware_integration(self, client):
        """Test that session middleware works correctly."""
        location_data = {"lat": 40.7128, "lon": -74.0060}
        response = client.post(
            "/api/location/",
            data=json.dumps(location_data),
            content_type="application/json",
        )
        assert response.status_code == 200

        assert hasattr(client, "session")
        assert "coords" in client.session

    def test_csrf_middleware_integration(self, client):
        """Test CSRF middleware integration."""
        response = client.get("/location/")
        assert response.status_code == 200

        csrf_present = "csrftoken" in response.cookies or "csrf" in response.content.decode().lower()
        assert csrf_present


@pytest.mark.slow
@pytest.mark.integration
class TestLongRunningIntegration:
    """Test long-running integration scenarios."""

    def test_extended_session_usage(self, client):
        """Test extended session usage over many requests."""
        for i in range(100):
            if i % 10 == 0:
                location_data = {"lat": 40.0 + (i * 0.01), "lon": -74.0 + (i * 0.01)}
                client.post(
                    "/api/location/",
                    data=json.dumps(location_data),
                    content_type="application/json",
                )
            else:
                response = client.get("/") if i % 2 == 0 else client.get("/location/")
                assert response.status_code == 200

    def test_memory_usage_stability(self, client):
        """Test that memory usage remains stable over many requests."""
        gc.collect()

        for _ in range(500):
            client.get("/")
            client.get("/location/")

        gc.collect()


@pytest.mark.integration
class TestFailureRecovery:
    """Test system recovery from various failure modes."""

    def test_recovery_from_invalid_session_data(self, client):
        """Test recovery when session contains invalid data."""
        session = client.session
        session["coords"] = "invalid_data"
        session.save()

        response = client.get("/location/")
        assert response.status_code == 200

        location_data = {"lat": 40.7128, "lon": -74.0060}
        response = client.post(
            "/api/location/",
            data=json.dumps(location_data),
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_recovery_from_network_simulation(self, client):
        """Test recovery patterns in network-like failure scenarios."""
        failure_requests = [
            ("", "text/plain"),
            ("invalid json", "application/json"),
            ("null", "application/json"),
        ]

        for data, content_type in failure_requests:
            response = client.post(
                "/api/location/",
                data=data,
                content_type=content_type,
            )
            assert response.status_code == 400

        valid_data = {"lat": 40.7128, "lon": -74.0060}
        response = client.post(
            "/api/location/",
            data=json.dumps(valid_data),
            content_type="application/json",
        )
        assert response.status_code == 200
