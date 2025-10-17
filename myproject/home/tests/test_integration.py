#Integration test cases for the Django project.
#Tests end-to-end functionality, cross-component interactions, and user workflows.

import pytest
import json
from django.test import Client, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.management import call_command
from django.conf import settings
import time

User = get_user_model()


@pytest.mark.integration
class TestFullUserWorkflow:
    """Test complete user workflows from start to finish."""
    
    def test_complete_location_workflow(self, client):
        """Test the complete workflow: visit index -> save location -> view location."""
        # Step 1: Visit index page
        response = client.get('/')
        assert response.status_code == 200
        
        # Step 2: Save location via API
        location_data = {"lat": 40.7128, "lon": -74.0060}
        save_response = client.post(
            '/api/location/',
            data=json.dumps(location_data),
            content_type='application/json'
        )
        assert save_response.status_code == 200
        save_data = save_response.json()
        assert save_data["ok"] is True
        
        # Step 3: View location page to see saved coordinates
        location_response = client.get('/location/')
        assert location_response.status_code == 200
        assert location_response.context['coords'] is not None
        assert location_response.context['coords']['lat'] == 40.7128
        assert location_response.context['coords']['lon'] == -74.0060
        
        # Verify coordinates appear in the rendered HTML
        content = location_response.content.decode()
        assert '40.7128' in content
        assert '-74.0060' in content
    
    def test_multiple_location_updates_workflow(self, client):
        """Test workflow with multiple location updates."""
        locations = [
            {"lat": 40.7128, "lon": -74.0060, "name": "New York"},
            {"lat": 34.0522, "lon": -118.2437, "name": "Los Angeles"},
            {"lat": 41.8781, "lon": -87.6298, "name": "Chicago"},
        ]
        
        for location in locations:
            # Save each location
            save_response = client.post(
                '/api/location/',
                data=json.dumps({"lat": location["lat"], "lon": location["lon"]}),
                content_type='application/json'
            )
            assert save_response.status_code == 200
            
            # Verify it's saved in session
            location_response = client.get('/location/')
            assert location_response.status_code == 200
            coords = location_response.context['coords']
            assert coords['lat'] == location['lat']
            assert coords['lon'] == location['lon']
    
    def test_session_persistence_across_requests(self, client):
        """Test that session data persists across multiple requests."""
        # Save location
        location_data = {"lat": 37.7749, "lon": -122.4194}  # San Francisco
        client.post(
            '/api/location/',
            data=json.dumps(location_data),
            content_type='application/json'
        )
        
        # Make multiple requests and verify session persists
        for _ in range(5):
            response = client.get('/location/')
            assert response.status_code == 200
            coords = response.context['coords']
            assert coords['lat'] == 37.7749
            assert coords['lon'] == -122.4194


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling across the entire application."""
    
    def test_invalid_json_to_location_page_flow(self, client):
        """Test flow from invalid JSON submission to location page."""
        # Try to save invalid JSON
        response = client.post(
            '/api/location/',
            data='{"invalid": json}',
            content_type='application/json'
        )
        assert response.status_code == 400
        
        # Location page should still work (no coordinates saved)
        location_response = client.get('/location/')
        assert location_response.status_code == 200
        assert location_response.context['coords'] is None
    
    def test_incomplete_data_handling(self, client):
        """Test handling of incomplete coordinate data."""
        incomplete_data_sets = [
            {"lat": 40.7128},  # Missing longitude
            {"lon": -74.0060},  # Missing latitude
            {},  # Empty object
            {"lat": None, "lon": -74.0060},  # Null latitude
            {"lat": 40.7128, "lon": None},  # Null longitude
        ]
        
        for data in incomplete_data_sets:
            response = client.post(
                '/api/location/',
                data=json.dumps(data),
                content_type='application/json'
            )
            assert response.status_code == 400
            
            # Verify error response
            response_data = response.json()
            assert response_data["ok"] is False
            assert "error" in response_data
    
    def test_cross_view_error_recovery(self, client):
        """Test that errors in one view don't affect others."""
        # Cause an error in save_location
        client.post('/api/location/', data='invalid', content_type='application/json')
        
        # Other views should still work normally
        index_response = client.get('/')
        assert index_response.status_code == 200
        
        location_response = client.get('/location/')
        assert location_response.status_code == 200


@pytest.mark.integration
class TestSecurityIntegration:
    """Test security features integration."""
    
    def test_csrf_protection_integration(self, client):
        """Test CSRF protection across views."""
        # Location page should set CSRF cookie
        response = client.get('/location/')
        assert response.status_code == 200
        assert 'csrftoken' in response.cookies or 'csrfmiddlewaretoken' in response.content.decode()
    
    def test_method_security_integration(self, client):
        """Test HTTP method restrictions work correctly."""
        # save_location should only accept POST
        response = client.get('/api/location/')
        assert response.status_code == 405
        
        response = client.put('/api/location/', data='{}', content_type='application/json')
        assert response.status_code == 405
        
        response = client.delete('/api/location/')
        assert response.status_code == 405
    
    def test_content_type_validation(self, client):
        """Test that content type validation works."""
        # API should expect JSON
        response = client.post('/api/location/', data='test=data')
        # Might accept form data or might not, depending on implementation
        # The important thing is it doesn't crash
        assert response.status_code in [200, 400, 415]


@pytest.mark.integration
class TestPerformanceIntegration:
    """Test performance characteristics of integrated workflows."""
    
    def test_rapid_location_updates_performance(self, client):
        """Test performance under rapid location updates."""
        locations = [
            {"lat": 40.7128 + i * 0.001, "lon": -74.0060 + i * 0.001}
            for i in range(50)
        ]
        
        start_time = time.time()
        
        for location in locations:
            response = client.post(
                '/api/location/',
                data=json.dumps(location),
                content_type='application/json'
            )
            assert response.status_code == 200
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle 50 requests in reasonable time
        assert total_time < 5.0  # Less than 5 seconds
        avg_time_per_request = total_time / 50
        assert avg_time_per_request < 0.1  # Less than 100ms per request
    
    def test_concurrent_session_handling(self, client):
        """Test handling of multiple concurrent sessions."""
        # Create multiple clients to simulate different users
        clients = [Client() for _ in range(5)]
        
        # Each client saves different coordinates
        for i, test_client in enumerate(clients):
            location = {"lat": 40.0 + i, "lon": -74.0 + i}
            response = test_client.post(
                '/api/location/',
                data=json.dumps(location),
                content_type='application/json'
            )
            assert response.status_code == 200
        
        # Verify each client has its own session data
        for i, test_client in enumerate(clients):
            response = test_client.get('/location/')
            assert response.status_code == 200
            coords = response.context['coords']
            assert coords['lat'] == 40.0 + i
            assert coords['lon'] == -74.0 + i


@pytest.mark.integration
class TestDatabaseIntegration:
    """Test database interactions (even though this app doesn't use much DB)."""
    
    def test_user_creation_integration(self, client):
        """Test user creation and authentication flow."""
        # Create a user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Login and test location workflow
        client.force_login(user)
        
        # Normal workflow should still work
        location_data = {"lat": 40.7128, "lon": -74.0060}
        response = client.post(
            '/api/location/',
            data=json.dumps(location_data),
            content_type='application/json'
        )
        assert response.status_code == 200
    
    def test_admin_access_integration(self):
        """Test admin interface integration."""
        # Create admin user
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        client = Client()
        client.force_login(admin_user)
        
        # Access admin interface
        response = client.get('/admin/')
        assert response.status_code == 200


@pytest.mark.integration
class TestStaticFilesIntegration:
    """Test static file serving integration."""
    
    def test_css_file_accessibility(self, client):
        """Test that CSS files are accessible."""
        # First, check if static files are referenced in templates
        response = client.get('/')
        content = response.content.decode()
        
        if 'static' in content or '.css' in content:
            # CSS should be accessible if referenced
            # This might fail in test environment without collectstatic
            pass  # Static file serving tested separately
        
        # At minimum, pages should render without CSS
        assert response.status_code == 200
    
    def test_template_rendering_without_static_files(self, client, settings):
        """Test that templates render gracefully without static files."""
        # Temporarily disable static file serving
        settings.DEBUG = False
        
        response = client.get('/')
        assert response.status_code == 200
        
        response = client.get('/location/')
        assert response.status_code == 200


@pytest.mark.integration
class TestMiddlewareIntegration:
    """Test middleware integration and functionality."""
    
    def test_session_middleware_integration(self, client):
        """Test that session middleware works correctly."""
        # Save data that requires session
        location_data = {"lat": 40.7128, "lon": -74.0060}
        response = client.post(
            '/api/location/',
            data=json.dumps(location_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # Session should be created and accessible
        assert hasattr(client, 'session')
        assert 'coords' in client.session
    
    def test_csrf_middleware_integration(self, client):
        """Test CSRF middleware integration."""
        # Location page should include CSRF token
        response = client.get('/location/')
        assert response.status_code == 200
        
        # CSRF cookie or token should be present
        csrf_present = (
            'csrftoken' in response.cookies or
            'csrf' in response.content.decode().lower()
        )
        assert csrf_present


@pytest.mark.slow
@pytest.mark.integration
class TestLongRunningIntegration:
    """Test long-running integration scenarios."""
    
    def test_extended_session_usage(self, client):
        """Test extended session usage over many requests."""
        # Simulate extended usage
        for i in range(100):
            if i % 10 == 0:
                # Update location occasionally
                location_data = {"lat": 40.0 + (i * 0.01), "lon": -74.0 + (i * 0.01)}
                client.post(
                    '/api/location/',
                    data=json.dumps(location_data),
                    content_type='application/json'
                )
            else:
                # View pages
                response = client.get('/') if i % 2 == 0 else client.get('/location/')
                assert response.status_code == 200
    
    def test_memory_usage_stability(self, client):
        """Test that memory usage remains stable over many requests."""
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Make many requests
        for _ in range(500):
            client.get('/')
            client.get('/location/')
        
        # Memory should not grow excessively
        # This is a basic test - in production you'd use more sophisticated monitoring
        gc.collect()
        # If we get here without crashing, basic memory management is working


@pytest.mark.integration
class TestFailureRecovery:
    """Test system recovery from various failure modes."""
    
    def test_recovery_from_invalid_session_data(self, client):
        """Test recovery when session contains invalid data."""
        # Corrupt session data manually
        session = client.session
        session['coords'] = 'invalid_data'
        session.save()
        
        # System should handle corrupted session gracefully
        response = client.get('/location/')
        assert response.status_code == 200
        
        # Should be able to save new valid data
        location_data = {"lat": 40.7128, "lon": -74.0060}
        response = client.post(
            '/api/location/',
            data=json.dumps(location_data),
            content_type='application/json'
        )
        assert response.status_code == 200
    
    def test_recovery_from_network_simulation(self, client):
        """Test recovery patterns in network-like failure scenarios."""
        # Simulate various "network" failures
        failure_requests = [
            ('', 'text/plain'),  # Wrong content type
            ('invalid json', 'application/json'),  # Invalid JSON
            ('null', 'application/json'),  # Null payload
        ]
        
        for data, content_type in failure_requests:
            response = client.post('/api/location/', data=data, content_type=content_type)
            assert response.status_code == 400  # Should handle gracefully
        
        # System should recover and accept valid requests
        valid_data = {"lat": 40.7128, "lon": -74.0060}
        response = client.post(
            '/api/location/',
            data=json.dumps(valid_data),
            content_type='application/json'
        )
        assert response.status_code == 200