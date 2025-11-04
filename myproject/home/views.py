from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import urllib.parse
import requests


@ensure_csrf_cookie
def index(request):
    # Main page with integrated location feature.
    coords = request.session.get("coords")
    return render(request, 'index.html', {"coords": coords})


@ensure_csrf_cookie
def location_page(request):
    """Display the location page with saved coordinates."""
    coords = request.session.get('coords', None)
    return render(request, 'location.html', {'coords': coords})


def reverse_geocode(lat, lon):
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json"
        }
        headers = {
            "User-Agent": "RecreoApp/1.0 (jpotter4@uccs.edu)"  # required by Nominatim
        }
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()  # triggers error for bad HTTP responses

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


def meters_to_miles(meters):
    return round(meters * 0.000621371, 2)


def activities_page(request):
    coords = request.session.get("coords")
    activities = []

    if coords and coords.get("lat") and coords.get("lon"):
        api_key = "BOT2I9wTsq89SHT3q0MHbW9kcMcRP1c9foOKiGj-GjacAa2lZAtZJYKUNhVtMm_sEArMZAV7WZYnF1kF24O8Cg2JgrRonzvHlGWpyIoCqEtR0Qg3QZJp5M8YHBj1aHYx"
        url = "https://api.yelp.com/v3/businesses/search"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "categories": "parks,golf,hiking,biking,playgrounds,swimmingpools,soccer,baseball,basketball",
            "limit": 10,
            "radius": 25000  # meters
        }

        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            businesses = data.get("businesses", [])
            print(f"Found {len(businesses)} businesses")
            for b in businesses:
                distance_miles = meters_to_miles(b.get("distance", 0))
                activities.append({
                    "name": b.get("name", "Unnamed"),
                    "description": ", ".join([cat['title'] for cat in b.get("categories", [])]),
                    "location": ", ".join(filter(None, [b.get("location", {}).get("address1"), b.get("location", {}).get("city")])),
                    "distance_miles": distance_miles,
                    "lat": b.get("coordinates", {}).get("latitude", 0),
                    "lon": b.get("coordinates", {}).get("longitude", 0),
                })
            if not activities:
                print("No activities parsed from API response")
        else:
            print(f"Yelp API Error: {response.status_code} - {response.text}")

    else:
        print("No location coordinates in session")

    return render(request, "activities.html", {"coords": coords, "activities": activities})


# New view for activity detail page
# It extracts the activity name from the URL and displays details.
def activity_detail(request, name):
    print(f"URL param: {name}")  # debug

    name_decoded = urllib.parse.unquote(name).strip().lower()
    print(f"Decoded param: {name_decoded}")  # debug

    coords = request.session.get("coords")
    activities = []

    selected = None
    if coords and coords.get("lat") and coords.get("lon"):
        api_key = "BOT2I9wTsq89SHT3q0MHbW9kcMcRP1c9foOKiGj-GjacAa2lZAtZJYKUNhVtMm_sEArMZAV7WZYnF1kF24O8Cg2JgrRonzvHlGWpyIoCqEtR0Qg3QZJp5M8YHBj1aHYx"
        url = "https://api.yelp.com/v3/businesses/search"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {
            "latitude": coords["lat"],  # Using latitude from session
            "longitude": coords["lon"],  # Using longitude from session
            "categories": "parks,golf,hiking,biking,playgrounds,swimmingpools,soccer,baseball,basketball,tennis,volleyball,sportsgrounds",
            "limit": 10,
            "radius": 25000  # meters
        }
        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            businesses = data.get("businesses", [])
            print("Business names returned:")
            for b in businesses:
                print(b.get("name", "Unnamed"))  # debug display all names
                distance_miles = meters_to_miles(b.get("distance", 0))
                activities.append({
                    "name": b.get("name", "Unnamed"),
                    "description": ", ".join([cat['title'] for cat in b.get("categories", [])]),
                    "location": ", ".join(filter(None, [b.get("location", {}).get("address1"), b.get("location", {}).get("city")])),
                    "distance_miles": distance_miles,
                    # EXTRA FIELDS:
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

            for act in activities:  # debug all cleaned names
                print(act["name"].strip().lower())
            selected = next((act for act in activities if act["name"].strip().lower() == name_decoded), None)
            print(f"Selected: {selected}")  # debug
        else:
            print(f"Yelp API error: {response.status_code} - {response.text}")

    if selected:
        return render(request, "activity_detail.html", {"activity": selected})
    else:
        return render(request, "activity_detail.html", {"activity": None})
