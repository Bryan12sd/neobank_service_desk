from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied


def group_required(*group_names):

    def in_groups(user):
        if user.is_authenticated and (
            user.is_superuser or user.groups.filter(name__in=group_names).exists()
        ):
            return True
        raise PermissionDenied

    def decorator(view_func):
        return login_required(user_passes_test(in_groups)(view_func))

    return decorator