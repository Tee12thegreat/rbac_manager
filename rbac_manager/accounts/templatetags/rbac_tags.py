from django import template

register = template.Library()


@register.filter
def has_perm(user, perm_string):
    """
    Usage: {% if request.user|has_perm:'Resource Name:ACTION' %}
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        resource_name, action = perm_string.split(':', 1)
        return user.profile.has_permission(resource_name.strip(), action.strip())
    except Exception:
        return False


@register.filter
def badge_class(severity):
    mapping = {
        'LOW':      'bg-info',
        'MEDIUM':   'bg-warning text-dark',
        'HIGH':     'bg-danger',
        'CRITICAL': 'bg-dark',
    }
    return mapping.get(severity, 'bg-secondary')


@register.filter
def status_badge(success):
    return 'bg-success' if success else 'bg-danger'
