from django.urls import path
from .views import index, location_page, save_location

urlpatterns = [
    path('', index, name='index'),
    path('location/', location_page, name='location_page'),
    path('api/location/', save_location, name='save_location'),
]
