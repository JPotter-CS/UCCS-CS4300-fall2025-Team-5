"""URL configuration for the home app."""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import index, save_location, location_page, activities_page, save_text_location
from . import views

urlpatterns = [
    path('', index, name='index'),
    path('api/location/', save_location, name='save_location'),
    path('save_text_location/', save_text_location, name='save_text_location'), 
    path('activities/', activities_page, name='activities'),
    path('activity/<str:name>/', views.activity_detail, name='activity_detail'),
    path('location/', location_page, name='location_page'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
