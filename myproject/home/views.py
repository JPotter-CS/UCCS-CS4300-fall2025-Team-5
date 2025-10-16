from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
import json

def index(request):
    return render(request, 'index.html')

@require_POST
def save_location(request):
    """Receive JSON lat/lon from the browser and store in session."""
    try:
        data = json.loads(request.body.decode("utf-8"))
        lat = float(data["lat"])
        lon = float(data["lon"])
    except Exception:
        return JsonResponse({"ok": False, "error": "Invalid data"}, status=400)

    # store coords in session so we can show them later
    request.session["coords"] = {"lat": lat, "lon": lon}
    return JsonResponse({"ok": True, "coords": request.session["coords"]})

from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def location_page(request):
    coords = request.session.get("coords")
    return render(request, "location.html", {"coords": coords})