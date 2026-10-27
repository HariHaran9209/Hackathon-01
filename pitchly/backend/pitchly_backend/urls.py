from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "healthy", "service": "pitchly-backend"})

urlpatterns = [
    path('', health_check, name='root-health'),
    path('health/', health_check, name='health'),
    path('api/health/', health_check, name='api-health'),
    path('admin/', admin.site.urls),
    path('api/', include('plans.urls')),
]
