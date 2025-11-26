from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrManagerOrReadOnly(BasePermission):
    """
    Read-only for everyone.
    Write operations allowed only for Admins or Store Managers.
    """

    def has_permission(self, request, view):
        # SAFE_METHODS: GET, HEAD, OPTIONS
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        # superuser always allowed
        if user.is_superuser:
            return True

        # Using our custom role helpers (if available)
        if hasattr(user, "is_admin") and user.is_admin():
            return True

        if hasattr(user, "is_store_manager") and user.is_store_manager():
            return True

        return False
