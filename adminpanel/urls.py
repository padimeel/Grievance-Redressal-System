from django.urls import path
from django.http import JsonResponse

def ping(request):
    return JsonResponse({ "status": "adminpanel OK" })

urlpatterns = [
    path("", ping, name="adminpanel-root"),
]
