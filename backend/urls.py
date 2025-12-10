# backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def redirect_to_adminpanel_reset(request):
    uid = request.GET.get('uid', '')
    token = request.GET.get('token', '')
    return redirect(f"/adminpanel/reset-password?uid={uid}&token={token}")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('adminpanel/', include('adminpanel.urls', namespace='adminpanel')),
    path('reset-password/', redirect_to_adminpanel_reset),  # add trailing slash
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('citizen/', include('citizen.urls', namespace='citizen')),
    path('officer/', include('officer.urls', namespace='officer')),
]





