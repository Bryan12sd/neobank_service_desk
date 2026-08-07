from django import template

register = template.Library()

STATUS_BADGE_CLASSES = {
    "OPEN": "badge-secondary",
    "ASSIGNED": "badge-info",
    "IN_PROGRESS": "badge-primary",
    "ON_HOLD": "badge-warning",
    "RESOLVED": "badge-success",
    "CLOSED": "badge-dark",
}


@register.filter
def status_badge_class(status):
    """Uso en template: <span class="badge {{ ticket.status|status_badge_class }}">"""
    return STATUS_BADGE_CLASSES.get(status, "badge-secondary")


@register.filter
def has_group(user, group_name):
    """Uso en template: {% if request.user|has_group:"AGENT" %}"""
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name=group_name).exists()