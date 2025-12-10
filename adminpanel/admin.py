from django.apps import apps
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.admin.sites import AlreadyRegistered

# --------------------------------
# Custom Admin Site
# --------------------------------
class CustomAdminSite(AdminSite):
    site_header = "Admin Panel"
    site_title = "Admin Portal"
    index_title = "Welcome to Admin Panel"


# Instance of custom admin site
admin_site = CustomAdminSite(name="custom_admin")


# --------------------------------
# Custom ModelAdmin classes
# --------------------------------
class GrievanceAdmin(admin.ModelAdmin):
    list_display = ("id", "tracking_id", "title", "status", "assigned_officer", "created_at")
    search_fields = (
        "title",
        "description",
        "tracking_id",
        "user__username",
        "assigned_officer__username",
    )
    list_filter = ("status", "category", "assigned_officer", "created_at")
    ordering = ("-created_at",)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "department")
    search_fields = ("name",)
    list_filter = ("department",)
    ordering = ("department", "name")


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code")
    search_fields = ("name", "code")
    ordering = ("name",)


class GrievanceRemarkAdmin(admin.ModelAdmin):
    list_display = ("id", "grievance", "officer", "created_at")
    search_fields = ("remark", "officer__username", "grievance__tracking_id")
    ordering = ("-created_at",)


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "grievance", "rating", "submitted_at")
    search_fields = ("grievance__tracking_id",)
    list_filter = ("rating",)
    ordering = ("-submitted_at",)


class ChangeLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "grievance", "action", "timestamp")
    search_fields = ("action", "user__username", "grievance__tracking_id")
    ordering = ("-timestamp",)


# -----------------------------------------
# Safe dynamic registration function
# -----------------------------------------
def register_if_exists(model_name, admin_class=None, app_label="adminpanel"):
    """
    Dynamically registers models with the custom admin site.
    Skips silently if model doesn't exist or is already registered.
    """
    try:
        model = apps.get_model(app_label, model_name)
        if admin_class:
            admin_site.register(model, admin_class)
        else:
            admin_site.register(model)
    except LookupError:
        # Model does not exist
        pass
    except AlreadyRegistered:
        # Prevent duplicate registration
        pass


# -----------------------------------------
# Register models to custom admin
# -----------------------------------------
register_if_exists("Department", DepartmentAdmin)
register_if_exists("Category", CategoryAdmin)
register_if_exists("Grievance", GrievanceAdmin)
register_if_exists("GrievanceRemark", GrievanceRemarkAdmin)
register_if_exists("Feedback", FeedbackAdmin)
register_if_exists("ChangeLog", ChangeLogAdmin)

