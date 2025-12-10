# accounts/permissions.py
from rest_framework import permissions

class IsAdminPanel(permissions.BasePermission):
    """
    Allows access only to users with role 'admin' or Django is_staff/superuser.
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.is_staff or getattr(user, 'role', None) == 'admin'))
