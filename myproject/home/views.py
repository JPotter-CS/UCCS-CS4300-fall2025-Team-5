from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import urllib.parse
import requests
import os


@ensure_csrf_cookie
def index(request):
    coords = request.session.get("coords")
    return render(request, 'index.html', {"coords": coords})


@ensure_csrf_cookie
def location_page(request):
    coords = request.session.get('coords', None)
    return render(request, 'location.html', {'coords': coords})


def reverse_geocode(lat, lon):
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json"}
        headers = {"User-Agent": "RecreoApp/1.0 (jpotter4@uccs.edu)"}
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        address = data.get("address", {})
        city = address.get("city") or address.get("town") or address.get("village") or "Unknown City"
        state = address.get("state") or address.get("region") or "Unknown State"
        return city, state
    except Exception as e:
        print("Reverse geocode error:", e)
        return "Unknown City", "Unknown State"


@require_POST
def save_location(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        lat = float(data["lat"])
        lon = float(data["lon"])
    except Exception:
        return JsonResponse({"ok": False, "error": "Invalid data"}, status=400)

    city, state = reverse_geocode(lat, lon)
    request.session["coords"] = {"lat": lat, "lon": lon, "city": city, "state": state}
    return JsonResponse({"ok": True, "coords": request.session["coords"]})


@require_POST
@csrf_exempt  # Can omit if your form has {% csrf_token %}
def save_text_location(request):
    city = request.POST.get('city', '').strip()
    state = request.POST.get('state', '').strip().upper()
    if city and state:
        lat, lon = geocode_city_state(city, state)
        if lat and lon:
            request.session['coords'] = {'city': city, 'state': state, 'lat': lat, 'lon': lon}
        else:
            request.session['coords'] = {'city': city, 'state': state}
        return redirect('activities')
    else:
        return redirect('index')


def meters_to_miles(meters):
    return round(meters * 0.000621371, 2)


def geocode_city_state(city, state):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"city": city, "state": state, "country": "United States", "format": "json"}
        headers = {"User-Agent": "RecreoApp/1.0 (jpotter4@uccs.edu)"}
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
        else:
            return None, None
    except Exception as e:
        print("Geocode error:", e)
        return None, None


def activities_page(request):
    coords = request.session.get("coords")
    activities = []

    # New filter parameters from the query string
    activity_type = request.GET.get("type", "")
    max_distance = request.GET.get("max_distance", "")
    min_rating = request.GET.get("min_rating", "")
    open_now = request.GET.get("open_now", "")
    
    # Prep coordinates if needed
    if coords and not (coords.get("lat") and coords.get("lon")) and coords.get("city") and coords.get("state"):
        lat, lon = geocode_city_state(coords["city"], coords["state"])
        if lat and lon:
            coords["lat"] = lat
            coords["lon"] = lon
            request.session["coords"] = coords

    if coords and coords.get("lat") and coords.get("lon"):
        api_key = os.getenv("YELP_API_KEY")
        url = "https://api.yelp.com/v3/businesses/search"
        headers = {"Authorization": f"Bearer {api_key}"}

        # Base categories for default search
        base_categories = "parks,golf,hiking,biking,playgrounds,swimmingpools,soccer,baseball,basketball"
        categories = activity_type if activity_type else base_categories

        # Yelp radius is in meters, default to 25000 if none selected
        radius = int(max_distance) * 1609 if max_distance else 25000  # 1 mile = 1609 meters

        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "categories": categories,
            "limit": 20,          # increase if you want
            "radius": radius,
        }

        if open_now:
            params["open_now"] = True

        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            businesses = data.get("businesses", [])
            for b in businesses:
                distance_miles = meters_to_miles(b.get("distance", 0))
                rating = b.get("rating", 0)
                
                # Apply min_rating filter in Python after fetching
                if min_rating and rating < float(min_rating):
                    continue

                activities.append({
                    "name": b.get("name", "Unnamed"),
                    "description": ", ".join([cat['title'] for cat in b.get("categories", [])]),
                    "location": ", ".join(filter(None, [b.get("location", {}).get("address1"), b.get("location", {}).get("city")])),
                    "distance_miles": distance_miles,
                    "lat": b.get("coordinates", {}).get("latitude", 0),
                    "lon": b.get("coordinates", {}).get("longitude", 0),
                    "rating": rating,
                    "is_closed": b.get("is_closed"),
                })
        else:
            print(f"Yelp API Error: {response.status_code} - {response.text}")
    else:
        print("No location coordinates in session")

    return render(request, "activities.html", {
        "coords": coords,
        "activities": activities,
        "selected_type": activity_type,
        "max_distance": max_distance,
        "min_rating": min_rating,
        "open_now": open_now,
    })




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
            "categories": "parks,golf,hiking,biking,playgrounds,swimmingpools,soccer,baseball,basketball,tennis,volleyball,sportsgrounds",
            "limit": 10,
            "radius": 25000  # meters
        }
        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            businesses = data.get("businesses", [])
            for b in businesses:
                distance_miles = meters_to_miles(b.get("distance", 0))
                activities.append({
                    "name": b.get("name", "Unnamed"),
                    "description": ", ".join([cat['title'] for cat in b.get("categories", [])]),
                    "location": ", ".join(filter(None, [b.get("location", {}).get("address1"), b.get("location", {}).get("city")])),
                    "distance_miles": distance_miles,
                    "phone": b.get("display_phone"),
                    "rating": b.get("rating"),
                    "review_count": b.get("review_count"),
                    "image_url": b.get("image_url"),
                    "yelp_url": b.get("url"),
                    "zip_code": b.get("location", {}).get("zip_code"),
                    "price": b.get("price"),
                    "is_closed": b.get("is_closed"),
                    "lat": b.get("coordinates", {}).get("latitude", 0),
                    "lon": b.get("coordinates", {}).get("longitude", 0)
                })
            selected = next((act for act in activities if act["name"].strip().lower() == name_decoded), None)
        else:
            print(f"Yelp API error: {response.status_code} - {response.text}")

    return render(request, "activity_detail.html", {"activity": selected})
