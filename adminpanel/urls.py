# adminpanel/urls.py
from django.urls import path
from .views import (
    # template views
    dashboard_view,
    grievances_list_view,
    grievance_detail_view,
    analytics_view,
    users_view,
    categories_view,
    # API views (now inside views.py)
    api_categories_list_create,
    api_category_detail,
    api_grievances_list,
    api_grievance_assign,
    api_grievance_add_remark,
)

app_name = "adminpanel"

urlpatterns = [
    # -----------------------
    # HTML (template) routes
    # -----------------------
    path("dashboard/", dashboard_view, name="dashboard"),

    # two name aliases for compatibility
    path("grievances/", grievances_list_view, name="grievances_list"),

    path("grievances/<int:pk>/", grievance_detail_view, name="grievance_detail"),

    path("analytics/", analytics_view, name="analytics"),
    path("users/", users_view, name="users"),

    # categories template (aliases)
    path("categories/", categories_view, name="categories"),
    path("categories/", categories_view, name="categories_list"),

    # -----------------------
    # API (function-based, serializer-driven) - mapped to views.py
    # -----------------------
    path("api/categories/", api_categories_list_create, name="api-categories-list"),
    path("api/categories/<int:pk>/", api_category_detail, name="api-category-detail"),

    path("api/grievances/", api_grievances_list, name="api-grievances-list"),
    path("api/grievances/<int:pk>/assign/", api_grievance_assign, name="api-grievance-assign"),
    path("api/grievances/<int:pk>/remarks/", api_grievance_add_remark, name="api-grievance-add-remark"),
]

