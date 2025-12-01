
from django.apps import apps
from django.contrib import admin
from .admin import admin_site  # adjust path if needed

def register_if_exists(model_name):
    for m in apps.get_models():
        if m.__name__.lower() == model_name.lower():
            try:
                admin_site.register(m)
            except admin.sites.AlreadyRegistered:
                pass

register_if_exists('Grievance')
register_if_exists('Category')