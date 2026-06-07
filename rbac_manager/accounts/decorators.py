from functools import wraps
from datetime import timedelta
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone


def get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')


def require_permission(resource_name, action):
    """
    Decorator that enforces RBAC on a view.
    Logs every access attempt and raises a ViolationLog on denial.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from .models import AccessLog, ViolationLog

            if not request.user.is_authenticated:
                return redirect('accounts:login')

            ip = get_client_ip(request)

            # Django superusers bypass RBAC (they are the "break-glass" account)
            if request.user.is_superuser:
                AccessLog.objects.create(
                    user=request.user, username=request.user.username,
                    resource=resource_name, action=action,
                    ip_address=ip, success=True, reason='Superuser bypass',
                )
                return view_func(request, *args, **kwargs)

            # Ensure the user has a profile
            try:
                profile = request.user.profile
            except Exception:
                messages.warning(request, 'Your account has no profile. Contact an administrator.')
                return redirect('accounts:dashboard')

            granted = profile.has_permission(resource_name, action)

            if granted:
                AccessLog.objects.create(
                    user=request.user, username=request.user.username,
                    resource=resource_name, action=action,
                    ip_address=ip, success=True,
                )
                return view_func(request, *args, **kwargs)

            # ── Access DENIED ─────────────────────────────────────────────
            AccessLog.objects.create(
                user=request.user, username=request.user.username,
                resource=resource_name, action=action,
                ip_address=ip, success=False,
                reason=f'Insufficient privileges for {action} on {resource_name}',
            )

            # Compute severity
            recent_count = ViolationLog.objects.filter(
                user=request.user,
                timestamp__gte=timezone.now() - timedelta(minutes=10),
            ).count()

            if recent_count >= 3:
                severity = 'CRITICAL'
            elif not profile.roles.filter(is_active=True).exists():
                severity = 'HIGH'
            elif profile.has_permission(resource_name, 'VIEW') and action != 'VIEW':
                severity = 'LOW'
            else:
                severity = 'MEDIUM'

            ViolationLog.objects.create(
                user=request.user, username=request.user.username,
                resource=resource_name, attempted_action=action,
                ip_address=ip, severity=severity,
                description=(
                    f'User "{request.user.username}" attempted to perform '
                    f'"{action}" on "{resource_name}" without sufficient privileges.'
                ),
            )

            messages.error(
                request,
                f'Access Denied — you do not have permission to {action.lower()} '
                f'"{resource_name}". This attempt has been logged.',
            )
            return redirect('accounts:dashboard')

        return wrapper
    return decorator
