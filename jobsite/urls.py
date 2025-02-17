from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin panel accessible at /admin/
    path('', include('jobs.urls')),   # Job listings accessible at the root URL
]
