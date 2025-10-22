#Test cases for views in the home Django app.
#Tests all view functionality including HTTP methods, error handling, and session management.


import pytest
import json
from django.test import Client
from django.urls import reverse
from django.http import JsonResponse
from unittest.mock import patch, Mock
from home.views import index, save_location, location_page


@pytest.mark.views
class TestIndexView:
    """Test cases for the index view."""
    
    def test_index_view_get_success(self, client):
        """Test that index view returns 200 and renders correct template."""
        response = client.get('/')
        assert response.status_code == 200
        assert 'index.html' in [t.name for t in response.templates]
    
    def test_index_view_url_name(self, client):
        """Test index view accessible by URL name."""
        url = reverse('index')
        response = client.get(url)
        assert response.status_code == 200
    
    def test_index_view_content_type(self, client):
        """Test that index view returns HTML content type."""
        response = client.get('/')
        assert response['content-type'].startswith('text/html')
    
    def test_index_view_context_data(self, client):
        """Test that index view provides expected context."""
        response = client.get('/')
        # Since index view doesn't pass explicit context, 
        # we just verify it doesn't error and renders properly
        assert response.status_code == 200
    
    @pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
    def test_index_view_other_methods_allowed(self, client, method):
        """Test that index view handles other HTTP methods gracefully."""
        response = getattr(client, method.lower())('/')
        # Django views by default accept all methods unless restricted
        assert response.status_code in [200, 405]


@pytest.mark.views
class TestSaveLocationView:
    """Test cases for the save_location view."""
    
    def test_save_location_valid_data(self, client, sample_coordinates):
        """Test save_location with valid coordinate data."""
        response = client.post(
            '/api/location/',
            data=json.dumps(sample_coordinates["valid"]),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "coords" in data
        assert data["coords"]["lat"] == 40.7128
        assert data["coords"]["lon"] == -74.0060
    
    def test_save_location_invalid_lat(self, client, sample_coordinates):
        """Test save_location with invalid latitude."""
        response = client.post(
            '/api/location/',
            data=json.dumps(sample_coordinates["invalid_lat"]),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False
        assert "error" in data
        assert data["error"] == "Invalid data"
    
    def test_save_location_invalid_lon(self, client, sample_coordinates):
        """Test save_location with invalid longitude."""
        response = client.post(
            '/api/location/',
            data=json.dumps(sample_coordinates["invalid_lon"]),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False
        assert data["error"] == "Invalid data"
    
    def test_save_location_missing_lat(self, client, sample_coordinates):
        """Test save_location with missing latitude."""
        response = client.post(
            '/api/location/',
            data=json.dumps(sample_coordinates["missing_lat"]),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False
        assert data["error"] == "Invalid data"
    
    def test_save_location_missing_lon(self, client, sample_coordinates):
        """Test save_location with missing longitude."""
        response = client.post(
            '/api/location/',
            data=json.dumps(sample_coordinates["missing_lon"]),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False
        assert data["error"] == "Invalid data"
    
    def test_save_location_invalid_json(self, client):
        """Test save_location with malformed JSON."""
        response = client.post(
            '/api/location/',
            data='{"invalid": json}',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False
        assert data["error"] == "Invalid data"
    
    def test_save_location_empty_data(self, client):
        """Test save_location with empty JSON object."""
        response = client.post(
            '/api/location/',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False
        assert data["error"] == "Invalid data"
    
    def test_save_location_session_storage(self, client, sample_coordinates):
        """Test that coordinates are properly stored in session."""
        response = client.post(
            '/api/location/',
            data=json.dumps(sample_coordinates["valid"]),
            content_type='application/json'
        )
        
        # Verify session contains the coordinates
        session = client.session
        assert 'coords' in session
        assert session['coords']['lat'] == 40.7128
        assert session['coords']['lon'] == -74.0060
    
    def test_save_location_get_method_not_allowed(self, client):
        """Test that GET method returns 405 Method Not Allowed."""
        response = client.get('/api/location/')
        assert response.status_code == 405
    
    def test_save_location_no_csrf_required(self, client, sample_coordinates):
        """Test that CSRF token is not required for API endpoint."""
        # This should work without CSRF token due to the view being an API endpoint
        response = client.post(
            '/api/location/',
            data=json.dumps(sample_coordinates["valid"]),
            content_type='application/json'
        )
        assert response.status_code == 200
    
    def test_save_location_extreme_coordinates(self, client):
        """Test save_location with extreme but valid coordinates."""
        extreme_coords = {"lat": -90.0, "lon": -180.0}
        response = client.post(
            '/api/location/',
            data=json.dumps(extreme_coords),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["coords"]["lat"] == -90.0
        assert data["coords"]["lon"] == -180.0
    
    @pytest.mark.parametrize("lat,lon", [
        (0, 0),  # Equator and Prime Meridian
        (90, 180),  # North Pole area, max longitude
        (-90, -180),  # South Pole area, min longitude
        (45.5, -122.7),  # Portland, OR coordinates
    ])
    def test_save_location_various_coordinates(self, client, lat, lon):
        """Test save_location with various valid coordinate combinations."""
        coords = {"lat": lat, "lon": lon}
        response = client.post(
            '/api/location/',
            data=json.dumps(coords),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["coords"]["lat"] == lat
        assert data["coords"]["lon"] == lon


@pytest.mark.views  
class TestLocationPageView:
    """Test cases for the location_page view."""
    
    def test_location_page_view_get_success(self, client):
        """Test that location page view returns 200."""
        response = client.get('/location/')
        assert response.status_code == 200
        assert 'location.html' in [t.name for t in response.templates]
    
    def test_location_page_url_name(self, client):
        """Test location page view accessible by URL name."""
        url = reverse('location_page')
        response = client.get(url)
        assert response.status_code == 200
    
    def test_location_page_with_session_coords(self, client_with_session):
        """Test location page when session has coordinates."""
        response = client_with_session.get('/location/')
        assert response.status_code == 200
        assert response.context['coords'] is not None
        assert response.context['coords']['lat'] == 40.7128
        assert response.context['coords']['lon'] == -74.0060
    
    def test_location_page_without_session_coords(self, client):
        """Test location page when session has no coordinates."""
        response = client.get('/location/')
        assert response.status_code == 200
        assert response.context['coords'] is None
    
    def test_location_page_context_data(self, client_with_session):
        """Test that location page provides correct context."""
        response = client_with_session.get('/location/')
        assert 'coords' in response.context
        coords = response.context['coords']
        assert isinstance(coords, dict)
        assert 'lat' in coords
        assert 'lon' in coords
    
    def test_location_page_csrf_cookie(self, client):
        """Test that location page includes CSRF cookie due to decorator."""
        response = client.get('/location/')
        assert response.status_code == 200
        # The @ensure_csrf_cookie decorator should set the CSRF cookie
        assert 'csrftoken' in response.cookies or 'csrfmiddlewaretoken' in str(response.content)
    
    @pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
    def test_location_page_other_methods_allowed(self, client, method):
        """Test that location page handles other HTTP methods."""
        response = getattr(client, method.lower())('/location/')
        # Should allow all methods since no restriction is set
        assert response.status_code in [200, 405]


@pytest.mark.integration
class TestViewIntegration:
    """Integration tests for view interactions."""
    
    def test_save_location_then_view_location_page(self, client, sample_coordinates):
        """Test full flow: save location via API, then view location page."""
        # First, save location coordinates
        save_response = client.post(
            '/api/location/',
            data=json.dumps(sample_coordinates["valid"]),
            content_type='application/json'
        )
        assert save_response.status_code == 200
        
        # Then, view the location page
        page_response = client.get('/location/')
        assert page_response.status_code == 200
        assert page_response.context['coords'] is not None
        assert page_response.context['coords']['lat'] == 40.7128
        assert page_response.context['coords']['lon'] == -74.0060
    
    def test_location_page_before_saving_coordinates(self, client):
        """Test viewing location page before saving any coordinates."""
        response = client.get('/location/')
        assert response.status_code == 200
        assert response.context['coords'] is None
    
    def test_multiple_coordinate_updates(self, client):
        """Test updating coordinates multiple times and viewing result."""
        coords_list = [
            {"lat": 40.7128, "lon": -74.0060},  # NYC
            {"lat": 34.0522, "lon": -118.2437},  # LA
            {"lat": 41.8781, "lon": -87.6298},   # Chicago
        ]
        
        for coords in coords_list:
            # Save coordinates
            save_response = client.post(
                '/api/location/',
                data=json.dumps(coords),
                content_type='application/json'
            )
            assert save_response.status_code == 200
            
            # Verify they're updated on the page
            page_response = client.get('/location/')
            assert page_response.status_code == 200
            assert page_response.context['coords']['lat'] == coords['lat']
            assert page_response.context['coords']['lon'] == coords['lon']


@pytest.mark.unit
class TestViewHelpers:
    """Test helper functions and utilities used by views."""
    
    def test_json_parsing_in_save_location(self, mock_post_request):
        """Test JSON parsing logic in save_location view."""
        # Test with valid data
        request = mock_post_request()
        response = save_location(request)
        assert isinstance(response, JsonResponse)
        
        # Parse the response
        response_data = json.loads(response.content)
        assert response_data["ok"] is True
    
    def test_session_handling_in_views(self, mock_request):
        """Test session handling across views."""
        # Test location_page view with mock request
        response = location_page(mock_request)
        assert response.status_code == 200
    
    """
    @patch('home.views.json.loads')
    def test_save_location_json_decode_error(self, mock_json_loads, mock_post_request):
        #Test save_location handles JSON decode errors properly.
        mock_json_loads.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        request = mock_post_request()
        response = save_location(request)
        
        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data["ok"] is False
        assert response_data["error"] == "Invalid data"
    """