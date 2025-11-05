from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

def index(request):
    return HttpResponse(
        # "<h2>Grievance Redressal API</h2>"
        # "<p>Available endpoints:</p>"
        # "<ul>"
        # "<li><a href='/admin/'>/admin/</a></li>"
        # "<li>/api/v1/citizen/register/ (POST)</li>"
        # "<li>/api/v1/citizen/grievances/ (GET/POST, JWT auth)</li>"
        # "<li>/api/token/ (POST username/password)</li>"
        # "</ul>",
        content_type="text/html"
    )

urlpatterns = [
    path('', index),                                      # root friendly page
    path('admin/', admin.site.urls),
    path('api/v1/citizen/', include('citizen.urls')),
    path('api/v1/officer/', include('officer.urls')),
    path('api/v1/adminpanel/', include('adminpanel.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]





