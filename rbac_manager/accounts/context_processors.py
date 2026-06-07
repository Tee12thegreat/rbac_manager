from .models import ViolationLog


def rbac_context(request):
    """Inject RBAC-related data into every template context."""
    if not request.user.is_authenticated:
        return {}

    ctx = {'is_superuser': request.user.is_superuser}

    if request.user.is_superuser:
        ctx['user_perms'] = {'ALL': True}
        ctx['open_violations'] = ViolationLog.objects.filter(is_resolved=False).count()
    else:
        try:
            profile = request.user.profile
            ctx['user_perms'] = profile.get_all_permissions()
            ctx['open_violations'] = ViolationLog.objects.filter(is_resolved=False).count()
        except Exception:
            ctx['user_perms'] = set()
            ctx['open_violations'] = 0

    return ctx
