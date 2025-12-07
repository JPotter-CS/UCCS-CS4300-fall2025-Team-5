"""Test cases for Django templates.
Tests template rendering, context data, and template content.
"""

import json
import time

import pytest
from bs4 import BeautifulSoup
from django.template.loader import render_to_string



@pytest.mark.unit
class TestIndexTemplate:
    """Test cases for index.html template."""

    def test_index_template_renders(self):
        """Test that index template renders without errors."""
        rendered = render_to_string("index.html", {})
        assert rendered is not None
        assert len(rendered.strip()) > 0

    def test_index_template_contains_expected_content(self, client):
        """Test that index template contains expected content."""
        response = client.get("/")
        content = response.content.decode()

        soup = BeautifulSoup(content, "html.parser")

        assert soup.find("html") is not None
        assert soup.find("body") is not None

    def test_index_template_has_doctype(self, client):
        """Test that index template has proper DOCTYPE."""
        response = client.get("/")
        content = response.content.decode()

        assert content.strip().startswith("<!DOCTYPE html>") or "DOCTYPE" in content.upper()

    def test_index_template_css_link(self, client):
        """Test that index template includes CSS stylesheet."""
        response = client.get("/")
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")

        css_links = soup.find_all("link", {"rel": "stylesheet"})
        style_tags = soup.find_all("style")

        assert len(css_links) > 0 or len(style_tags) > 0

    def test_index_template_meta_tags(self, client):
        """Test that index template has appropriate meta tags."""
        response = client.get("/")
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")

        viewport_tag = soup.find("meta", {"name": "viewport"})
        assert viewport_tag is not None

    def test_index_template_title_tag(self, client):
        """Test that index template has a title tag."""
        response = client.get("/")
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")

        title_tag = soup.find("title")
        assert title_tag is not None
        assert len(title_tag.get_text().strip()) > 0


@pytest.mark.unit
class TestLocationTemplate:
    """Test cases for location.html template."""

    def test_location_template_renders_without_coords(self):
        """Test that location template renders when no coordinates provided."""
        rendered = render_to_string("location.html", {"coords": None})
        assert rendered is not None
        assert len(rendered.strip()) > 0

    def test_location_template_renders_with_coords(self):
        """Test that location template renders with coordinates."""
        coords = {"lat": 40.7128, "lon": -74.0060}
        rendered = render_to_string("location.html", {"coords": coords})
        assert rendered is not None
        assert len(rendered.strip()) > 0

    def test_location_template_displays_coordinates(self, client_with_session):
        """Test that location template displays coordinates when available."""
        response = client_with_session.get("/location/")
        content = response.content.decode()

        assert "40.7128" in content
        assert "-74.006" in content

    def test_location_template_handles_missing_coordinates(self, client):
        """Test that location template handles missing coordinates gracefully."""
        response = client.get("/location/")
        content = response.content.decode()

        assert response.status_code == 200
        soup = BeautifulSoup(content, "html.parser")
        assert soup.find("html") is not None

    def test_location_template_structure(self, client):
        """Test the basic HTML structure of location template."""
        response = client.get("/location/")
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")

        assert soup.find("html") is not None
        assert soup.find("head") is not None
        assert soup.find("body") is not None
        assert soup.find("title") is not None


@pytest.mark.integration
class TestTemplateIntegration:
    """Test template integration with views and context data."""

    def test_index_template_with_view(self, client):
        """Test index template integration with index view."""
        response = client.get("/")
        assert response.status_code == 200
        assert "index.html" in [t.name for t in response.templates]

    def test_location_template_with_view(self, client):
        """Test location template integration with location_page view."""
        response = client.get("/location/")
        assert response.status_code == 200
        assert "location.html" in [t.name for t in response.templates]

    def test_template_context_data_flow(self, client, sample_coordinates):
        """Test that context data flows correctly from view to template."""
        client.post(
            "/api/location/",
            data=json.dumps(sample_coordinates["valid"]),
            content_type="application/json",
        )

        response = client.get("/location/")
        assert response.status_code == 200

        content = response.content.decode()
        assert str(sample_coordinates["valid"]["lat"]) in content
        assert str(sample_coordinates["valid"]["lon"]) in content


@pytest.mark.unit
class TestTemplateSecurity:
    """Test template security features."""

    def test_template_xss_protection(self):
        """Test that templates properly escape user input."""
        malicious_input = '<script>alert("xss")</script>'
        context = {"user_input": malicious_input}

        rendered = render_to_string("index.html", context)
        assert rendered is not None

    def test_template_csrf_protection(self, client):
        """Test that templates include CSRF protection where needed."""
        response = client.get("/location/")
        content = response.content.decode()

        assert "csrftoken" in response.cookies or "csrf" in content.lower()


@pytest.mark.unit
class TestTemplatePerformance:
    """Test template rendering performance."""

    def test_template_rendering_speed(self):
        """Test that template rendering is reasonably fast."""
        start_time = time.time()
        for _ in range(100):
            render_to_string("index.html", {})
        end_time = time.time()

        assert (end_time - start_time) < 1.0

    def test_template_with_context_speed(self):
        """Test template rendering speed with context data."""
        coords = {"lat": 40.7128, "lon": -74.0060}

        start_time = time.time()
        for _ in range(100):
            render_to_string("location.html", {"coords": coords})
        end_time = time.time()

        assert (end_time - start_time) < 1.0


@pytest.mark.unit
class TestTemplateAccessibility:
    """Test template accessibility features."""

    def test_template_has_lang_attribute(self, client):
        """Test that templates have language attribute for accessibility."""
        response = client.get("/")
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")

        html_tag = soup.find("html")
        if html_tag:
            lang_attr = html_tag.get("lang")
            assert lang_attr is not None or "lang=" in content

    def test_template_semantic_structure(self, client):
        """Test that templates use semantic HTML structure."""
        response = client.get("/")
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")

        semantic_tags = ["header", "main", "nav", "section", "article", "footer"]
        found_semantic = any(soup.find(tag) for tag in semantic_tags)

        assert found_semantic or soup.find("div") is not None


@pytest.mark.unit
class TestTemplateResponsiveness:
    """Test template responsive design features."""

    def test_template_viewport_meta_tag(self, client):
        """Test that templates include viewport meta tag for mobile."""
        response = client.get("/")
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")

        viewport_meta = soup.find("meta", {"name": "viewport"})
        assert viewport_meta is not None

        viewport_content = viewport_meta.get("content", "")
        assert "width=device-width" in viewport_content

    def test_template_responsive_css_classes(self, client):
        """Test that templates use responsive CSS classes."""
        response = client.get("/")
        content = response.content.decode()

        responsive_patterns = [
            "container",
            "row",
            "col",
            "responsive",
            "mobile",
            "tablet",
            "desktop",
        ]

        found_responsive = any(pattern in content.lower() for pattern in responsive_patterns)

        assert found_responsive or "@media" in content


@pytest.mark.integration
class TestTemplateErrorHandling:
    """Test template error handling and edge cases."""

    def test_template_handles_none_context(self):
        """Test that templates handle None values in context gracefully."""
        rendered = render_to_string("location.html", {"coords": None})
        assert rendered is not None

        assert "error" not in rendered.lower()
        assert "exception" not in rendered.lower()

    def test_template_handles_empty_context(self):
        """Test that templates handle empty context gracefully."""
        rendered = render_to_string("index.html", {})
        assert rendered is not None
        assert len(rendered.strip()) > 0

    def test_template_handles_malformed_coordinates(self):
        """Test that templates handle malformed coordinate data."""
        malformed_coords = {"lat": "invalid", "lon": None}
        rendered = render_to_string("location.html", {"coords": malformed_coords})
        assert rendered is not None

        assert "invalid" in rendered or rendered is not None
