# backend/citizen/permissions.py
from rest_framework import permissions

class IsAuthenticatedAndCitizen(permissions.BasePermission):
    """Require authentication for create/list operations (all authenticated users allowed to access; viewset will filter queryset)."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

class IsOwnerOrOfficerOrAdmin(permissions.BasePermission):
    """Object-level permission: owners can view; officers/admin can view & update; owners cannot change status/assignment."""
    def has_object_permission(self, request, view, obj):
        # Safe methods: owners or officers/admin
        if request.method in permissions.SAFE_METHODS:
            if obj.user == request.user:
                return True
            if getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False) or getattr(request.user, 'role', None) in ('officer','admin'):
                return True
            return False

        # Non-safe (PATCH/PUT/DELETE): allow only officer/admin to modify status/assignment
        if getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False) or getattr(request.user, 'role', None) in ('officer','admin'):
            return True

        # otherwise deny
        return False
