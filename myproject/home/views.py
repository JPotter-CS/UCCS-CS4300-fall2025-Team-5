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
    url = f"https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }
    response = requests.get(url, params=params, headers={"User-Agent": "yourproject 1.0"})
    data = response.json()
    address = data.get("address", {})
    city = address.get("city") or address.get("town") or address.get("village") or ""
    state = address.get("state") or address.get("region") or ""
    return city, state

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
