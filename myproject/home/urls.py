from django.urls import path
from .views import index, save_location, activities_page
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', index, name='index'),
    path('api/location/', save_location, name='save_location'),
    path('activities/', activities_page, name='activities'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)