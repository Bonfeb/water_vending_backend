from rest_framework.permissions import BasePermission


class IsStaffMember(BasePermission):
    """Allow access only to users in the 'staff' group."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name='staff').exists()
        )


class IsCustomer(BasePermission):
    """Allow access only to users in the 'customers' group."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name='customers').exists()
        )