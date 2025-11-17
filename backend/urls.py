# project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # auth & HTML login/register routes
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # role apps
    path('citizen/', include('citizen.urls', namespace='citizen')),
    path('officer/', include('officer.urls', namespace='officer')),
    path('adminpanel/', include('adminpanel.urls', namespace='adminpanel')), # use your admin app path
]




