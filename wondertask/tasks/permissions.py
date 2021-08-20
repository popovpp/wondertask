from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.creator == request.user


class PermissionPost(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_permission(self, request, view):
        if request.method == 'POST':
            return True
        else:
            return False


class IsExecutorOrObserver(permissions.BasePermission):
    """
    Custom permission to only allow executor or observer of an object
    """
    def has_object_permission(self, request, view, obj):
        if request.user.id in obj.executors.all().values_list("executor", flat=True):
            return True
        elif request.user.id in obj.observers.all().values_list("observer", flat=True):
            return True
        else:
            return False


