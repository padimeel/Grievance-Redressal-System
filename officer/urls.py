from django.urls import path
from django.http import JsonResponse

def ping(request):
    return JsonResponse({"status": "officer OK"})

urlpatterns = [
    path('', ping, name='officer-root'),


]