from rest_framework.permissions import BasePermission, SAFE_METHODS

class HasAnyRole(BasePermission):
    def __init__(self, *roles): self.roles = set(roles)
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.roles.filter(name__in=self.roles).exists())

class IsSupervisorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        if request.method in SAFE_METHODS:
            return bool(u and u.is_authenticated)
        return bool(u and u.is_authenticated and u.roles.filter(name__in=["SUPERVISOR","ADMIN"]).exists())

class IsWorkstationAuthenticated(BasePermission):
    """
    Mengizinkan akses hanya jika user sudah login melalui Workstation.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)