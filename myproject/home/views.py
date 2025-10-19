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
        lat = coords["lat"]
        lon = coords["lon"]
        api_key = "5ae2e3f221c38a28845f05b61345ed6b877f231fdde9f916173c536a"
        radius = 1000  # 1km search radius

        url = "https://api.opentripmap.com/0.1/en/places/radius"
        params = {
            "radius": radius,
            "lon": lon,
            "lat": lat,
            "kinds": "sport,amusements,adult,interesting_places,natural",  # recreational activities
            "format": "json",
            "apikey": api_key
        }
        try:
            response = requests.get(url, params=params, timeout=6)
            response.raise_for_status()
            places = response.json()
            # Limit to 10 places for simplicity
            for place in places[:10]:
                name = place.get("name", "Unnamed activity")
                kinds = place.get("kinds", "").replace(",", ", ")
                distance = round(place.get("dist", 0))
                activities.append({
                    "name": name,
                    "description": kinds.title(),
                    "location": f"{distance} meters from you"
                })
        except Exception as e:
            print("OpenTripMap error:", e)
    return render(request, "activities.html", {"coords": coords, "activities": activities})


