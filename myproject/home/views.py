from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import requests

@ensure_csrf_cookie
def index(request):
    #Main page with integrated location feature.
    coords = request.session.get("coords")
    return render(request, 'index.html', {"coords": coords})

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
            "categories": "active,fitness,arts,localflavor",  # recreational categories
            "limit": 10,
            "radius": 10000  # in meters (10 km)
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            businesses = data.get("businesses", [])
            for b in businesses:
                activities.append({
                    "name": b.get("name"),
                    "description": ", ".join(b.get("categories", []))[1:-1] if b.get("categories") else "",
                    "location": b.get("location", {}).get("address1", "") + ", " + b.get("location", {}).get("city", "")
                })
        except Exception as e:
            print("Yelp API error:", e)

    return render(request, "activities.html", {"coords": coords, "activities": activities})



