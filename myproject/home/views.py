"""Views for the home app: location handling and activity search."""

import json
import os
import urllib.parse

import requests
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST


@ensure_csrf_cookie
def index(request):
    """Render the index page with any stored coordinates."""
    coords = request.session.get("coords")
    return render(request, "index.html", {"coords": coords})


@ensure_csrf_cookie
def location_page(request):
    """Render the location page with any stored coordinates."""
    coords = request.session.get("coords", None)
    return render(request, "location.html", {"coords": coords})


def reverse_geocode(lat, lon):
    """Convert latitude/longitude to city/state using Nominatim."""
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"lat": lat, "lon": lon, "format": "json"}
    headers = {"User-Agent": "RecreoApp/1.0 (jpotter4@uccs.edu)"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        print("Reverse geocode error:", exc)
        return "Unknown City", "Unknown State"

    address = data.get("address", {})
    city = address.get("city") or address.get("town") or address.get("village") or "Unknown City"
    state = address.get("state") or address.get("region") or "Unknown State"
    return city, state


@require_POST
def save_location(request):
    """Save lat/lon to session after reverse geocoding; return JSON."""
    try:
        data = json.loads(request.body.decode("utf-8"))
        lat = float(data["lat"])
        lon = float(data["lon"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid data"}, status=400)

    city, state = reverse_geocode(lat, lon)
    request.session["coords"] = {"lat": lat, "lon": lon, "city": city, "state": state}
    return JsonResponse({"ok": True, "coords": request.session["coords"]})


@require_POST
@csrf_exempt  # Can omit if your form has {% csrf_token %}
def save_text_location(request):
    """Accept city/state text input, geocode, store in session, redirect."""
    city = request.POST.get("city", "").strip()
    state = request.POST.get("state", "").strip().upper()
    if not (city and state):
        return redirect("index")

    lat, lon = geocode_city_state(city, state)
    if lat is not None and lon is not None:
        request.session["coords"] = {"city": city, "state": state, "lat": lat, "lon": lon}
    else:
        request.session["coords"] = {"city": city, "state": state}
    return redirect("activities")


def meters_to_miles(meters):
    """Convert meters to miles, rounded to 2 decimals."""
    return round(meters * 0.000621371, 2)


def geocode_city_state(city, state):
    """Convert city/state to lat/lon using Nominatim."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "city": city,
        "state": state,
        "country": "United States",
        "format": "json",
    }
    headers = {"User-Agent": "RecreoApp/1.0 (jpotter4@uccs.edu)"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        print("Geocode error:", exc)
        return None, None

    if not data:
        return None, None

    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])
    return lat, lon


def activities_page(request):
    """List nearby activities using Yelp, honoring filters and session coords."""
    coords = request.session.get("coords")
    activities = []

    activity_type = request.GET.get("type", "")
    max_distance = request.GET.get("max_distance", "")
    min_rating = request.GET.get("min_rating", "")
    open_now = request.GET.get("open_now", "")

    if (
        coords
        and not (coords.get("lat") and coords.get("lon"))
        and coords.get("city")
        and coords.get("state")
    ):
        lat, lon = geocode_city_state(coords["city"], coords["state"])
        if lat is not None and lon is not None:
            coords["lat"] = lat
            coords["lon"] = lon
            request.session["coords"] = coords

    if coords and coords.get("lat") and coords.get("lon"):
        api_key = os.getenv("YELP_API_KEY")
        url = "https://api.yelp.com/v3/businesses/search"
        headers = {"Authorization": f"Bearer {api_key}"}

        base_categories = (
            "parks,golf,hiking,biking,playgrounds,swimmingpools,"
            "soccer,baseball,basketball"
        )
        categories = activity_type if activity_type else base_categories

        radius = int(max_distance) * 1609 if max_distance else 25000  # 1 mile ≈ 1609 m

        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "categories": categories,
            "limit": 20,
            "radius": radius,
        }

        if open_now:
            params["open_now"] = True

        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            businesses = data.get("businesses", [])
            for business in businesses:
                distance_miles = meters_to_miles(business.get("distance", 0))
                rating = business.get("rating", 0)

                if min_rating and rating < float(min_rating):
                    continue

                activities.append(
                    {
                        "name": business.get("name", "Unnamed"),
                        "description": ", ".join(
                            [cat["title"] for cat in business.get("categories", [])]
                        ),
                        "location": ", ".join(
                            filter(
                                None,
                                [
                                    business.get("location", {}).get("address1"),
                                    business.get("location", {}).get("city"),
                                ],
                            )
                        ),
                        "distance_miles": distance_miles,
                        "lat": business.get("coordinates", {}).get("latitude", 0),
                        "lon": business.get("coordinates", {}).get("longitude", 0),
                        "rating": rating,
                        "is_closed": business.get("is_closed"),
                    }
                )
        else:
            print(f"Yelp API Error: {response.status_code} - {response.text}")
    else:
        print("No location coordinates in session")

    return render(
        request,
        "activities.html",
        {
            "coords": coords,
            "activities": activities,
            "selected_type": activity_type,
            "max_distance": max_distance,
            "min_rating": min_rating,
            "open_now": open_now,
        },
    )


from ai_client.clients import generate_activity_description

def activity_detail(request, name):
    print(f"URL param: {name}")

    name_decoded = urllib.parse.unquote(name).strip().lower()
    print(f"Decoded param: {name_decoded}")

    coords = request.session.get("coords")
    activities = []
    selected = None

    if coords and coords.get("lat") and coords.get("lon"):
        api_key = os.getenv("YELP_API_KEY")
        url = "https://api.yelp.com/v3/businesses/search"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "categories": (
                "parks,golf,hiking,biking,playgrounds,swimmingpools,"
                "soccer,baseball,basketball,tennis,volleyball,sportsgrounds"
            ),
            "limit": 10,
            "radius": 25000,
        }
        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            businesses = data.get("businesses", [])
            for business in businesses:
                distance_miles = meters_to_miles(business.get("distance", 0))
                activity = {
                    "name": business.get("name", "Unnamed"),
                    "description": ", ".join(
                        [cat["title"] for cat in business.get("categories", [])]
                    ),
                    "location": ", ".join(
                        filter(
                            None,
                            [
                                business.get("location", {}).get("address1"),
                                business.get("location", {}).get("city"),
                            ],
                        )
                    ),
                    "distance_miles": distance_miles,
                    "phone": business.get("display_phone"),
                    "rating": business.get("rating"),
                    "review_count": business.get("review_count"),
                    "image_url": business.get("image_url"),
                    "yelp_url": business.get("url"),
                    "zip_code": business.get("location", {}).get("zip_code"),
                    "price": business.get("price"),
                    "is_closed": business.get("is_closed"),
                    "lat": business.get("coordinates", {}).get("latitude", 0),
                    "lon": business.get("coordinates", {}).get("longitude", 0),
                }
                # AI-generated description
                activity["ai_description"] = generate_activity_description(activity["name"])
                activities.append(activity)
            selected = next(
                (
                    act
                    for act in activities
                    if act["name"].strip().lower() == name_decoded
                ),
                None,
            )
        else:
            print(f"Yelp API error: {response.status_code} - {response.text}")

    return render(request, "activity_detail.html", {"activity": selected})

