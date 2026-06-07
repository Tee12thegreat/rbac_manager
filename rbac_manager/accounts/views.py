import csv
import json
from datetime import timedelta, date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpResponse
from django.utils import timezone

from .models import (
    Department, Resource, Permission, Role,
    UserProfile, AccessLog, ViolationLog,
)
from .forms import (
    StyledAuthForm, UserCreateForm, UserEditForm, RoleForm,
    ResourceForm, AccessLogFilterForm, ViolationFilterForm, ResolveViolationForm,
)
from .decorators import require_permission


# ─── Authentication ────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    form = StyledAuthForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Log the login event
            AccessLog.objects.create(
                user=user, username=user.username,
                resource='Authentication', action='VIEW',
                ip_address=_get_ip(request), success=True,
                reason='User login',
            )
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('accounts:dashboard')
        else:
            # Log failed login
            username = request.POST.get('username', 'unknown')
            AccessLog.objects.create(
                user=None, username=username,
                resource='Authentication', action='VIEW',
                ip_address=_get_ip(request), success=False,
                reason='Invalid credentials',
            )
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        AccessLog.objects.create(
            user=request.user, username=request.user.username,
            resource='Authentication', action='VIEW',
            ip_address=_get_ip(request), success=True,
            reason='User logout',
        )
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


# ─── Dashboard ─────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    today = timezone.now().date()
    seven_days_ago = timezone.now() - timedelta(days=6)

    # Summary stats
    total_users      = User.objects.filter(is_active=True).count()
    total_roles      = Role.objects.filter(is_active=True).count()
    total_resources  = Resource.objects.count()
    open_violations  = ViolationLog.objects.filter(is_resolved=False).count()
    today_access     = AccessLog.objects.filter(timestamp__date=today).count()
    today_denied     = AccessLog.objects.filter(timestamp__date=today, success=False).count()

    # Chart: access per day (last 7 days)
    labels, success_data, failed_data = [], [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        day_qs = AccessLog.objects.filter(timestamp__date=d)
        labels.append(d.strftime('%d %b'))
        success_data.append(day_qs.filter(success=True).count())
        failed_data.append(day_qs.filter(success=False).count())

    # Chart: users per role
    role_labels = list(Role.objects.filter(is_active=True).values_list('name', flat=True))
    role_counts = [Role.objects.get(name=n).members.filter(user__is_active=True).count()
                   for n in role_labels]

    recent_logs       = AccessLog.objects.select_related('user').all()[:10]
    recent_violations = ViolationLog.objects.filter(is_resolved=False).select_related('user')[:5]

    return render(request, 'accounts/dashboard.html', {
        'total_users': total_users, 'total_roles': total_roles,
        'total_resources': total_resources, 'open_violations': open_violations,
        'today_access': today_access, 'today_denied': today_denied,
        'chart_labels':   json.dumps(labels),
        'chart_success':  json.dumps(success_data),
        'chart_failed':   json.dumps(failed_data),
        'role_labels':    json.dumps(role_labels),
        'role_counts':    json.dumps(role_counts),
        'recent_logs':    recent_logs,
        'recent_violations': recent_violations,
    })


# ─── User Management ───────────────────────────────────────────────────────

@login_required
@require_permission('User Management', 'VIEW')
def user_list(request):
    qs = User.objects.select_related('profile', 'profile__department').prefetch_related('profile__roles').all()
    q = request.GET.get('q', '')
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q) |
                       Q(last_name__icontains=q) | Q(email__icontains=q))
    paginator = Paginator(qs, 15)
    page_obj  = paginator.get_page(request.GET.get('page'))
    return render(request, 'accounts/users/list.html', {'page_obj': page_obj, 'q': q})


@login_required
@require_permission('User Management', 'CREATE')
def user_create(request):
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        user = User.objects.create_user(
            username=cd['username'], email=cd['email'],
            password=cd['password1'],
            first_name=cd['first_name'], last_name=cd['last_name'],
            is_active=cd.get('is_active', True),
        )
        profile = UserProfile.objects.create(
            user=user, department=cd.get('department'),
            employee_id=cd.get('employee_id') or None,
            phone=cd.get('phone', ''),
        )
        profile.roles.set(cd.get('roles', []))
        messages.success(request, f'User "{user.username}" created successfully.')
        return redirect('accounts:user_list')
    departments = Department.objects.all()
    roles_by_resource = _roles_grouped()
    return render(request, 'accounts/users/form.html', {
        'form': form, 'action': 'Create', 'departments': departments,
        'roles_by_resource': roles_by_resource,
    })


@login_required
@require_permission('User Management', 'EDIT')
def user_edit(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)

    initial = {
        'first_name': target_user.first_name, 'last_name': target_user.last_name,
        'email': target_user.email, 'employee_id': profile.employee_id,
        'phone': profile.phone, 'department': profile.department,
        'roles': profile.roles.all(), 'is_active': target_user.is_active,
    }
    form = UserEditForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        target_user.first_name = cd['first_name']
        target_user.last_name  = cd['last_name']
        target_user.email      = cd['email']
        target_user.is_active  = cd.get('is_active', True)
        if cd.get('new_password'):
            target_user.set_password(cd['new_password'])
        target_user.save()
        profile.department  = cd.get('department')
        profile.employee_id = cd.get('employee_id') or None
        profile.phone       = cd.get('phone', '')
        profile.save()
        profile.roles.set(cd.get('roles', []))
        messages.success(request, f'User "{target_user.username}" updated.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/users/form.html', {
        'form': form, 'action': 'Edit', 'target_user': target_user,
    })


@login_required
@require_permission('User Management', 'DELETE')
def user_delete(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('accounts:user_list')
    if request.method == 'POST':
        name = target_user.username
        target_user.delete()
        messages.success(request, f'User "{name}" deleted.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/users/confirm_delete.html', {'target_user': target_user})


@login_required
@require_permission('User Management', 'VIEW')
def user_detail(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    user_logs   = AccessLog.objects.filter(user=target_user)[:20]
    user_viols  = ViolationLog.objects.filter(user=target_user)[:20]
    return render(request, 'accounts/users/detail.html', {
        'target_user': target_user, 'profile': profile,
        'user_logs': user_logs, 'user_viols': user_viols,
    })


# ─── Role Management ───────────────────────────────────────────────────────

@login_required
@require_permission('Role Management', 'VIEW')
def role_list(request):
    roles = Role.objects.prefetch_related('permissions', 'members').all()
    return render(request, 'accounts/roles/list.html', {'roles': roles})


@login_required
@require_permission('Role Management', 'CREATE')
def role_create(request):
    form = RoleForm(request.POST or None)
    resources = Resource.objects.prefetch_related('permissions').all()
    if request.method == 'POST' and form.is_valid():
        role = form.save()
        messages.success(request, f'Role "{role.name}" created.')
        return redirect('accounts:role_list')
    return render(request, 'accounts/roles/form.html', {
        'form': form, 'action': 'Create', 'resources': resources,
    })


@login_required
@require_permission('Role Management', 'EDIT')
def role_edit(request, pk):
    role      = get_object_or_404(Role, pk=pk)
    resources = Resource.objects.prefetch_related('permissions').all()
    form      = RoleForm(request.POST or None, instance=role)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Role "{role.name}" updated.')
        return redirect('accounts:role_list')
    return render(request, 'accounts/roles/form.html', {
        'form': form, 'action': 'Edit', 'role': role, 'resources': resources,
    })


@login_required
@require_permission('Role Management', 'DELETE')
def role_delete(request, pk):
    role = get_object_or_404(Role, pk=pk)
    if request.method == 'POST':
        if role.members.exists():
            messages.error(request, f'Cannot delete "{role.name}": it has active users assigned.')
            return redirect('accounts:role_list')
        role.delete()
        messages.success(request, f'Role "{role.name}" deleted.')
        return redirect('accounts:role_list')
    return render(request, 'accounts/roles/confirm_delete.html', {'role': role})


# ─── Resource Management ───────────────────────────────────────────────────

@login_required
@require_permission('Resource Management', 'VIEW')
def resource_list(request):
    resources = Resource.objects.prefetch_related('permissions').all()
    return render(request, 'accounts/resources/list.html', {'resources': resources})


@login_required
@require_permission('Resource Management', 'CREATE')
def resource_create(request):
    form = ResourceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        resource = form.save()
        for action in form.cleaned_data['actions']:
            Permission.objects.get_or_create(resource=resource, action=action)
        messages.success(request, f'Resource "{resource.name}" created with {len(form.cleaned_data["actions"])} permissions.')
        return redirect('accounts:resource_list')
    return render(request, 'accounts/resources/form.html', {'form': form})


# ─── Access Logs ───────────────────────────────────────────────────────────

@login_required
@require_permission('Access Logs', 'VIEW')
def access_logs(request):
    qs   = AccessLog.objects.select_related('user').all()
    form = AccessLogFilterForm(request.GET or None)
    if form.is_valid():
        cd = form.cleaned_data
        if cd.get('date_from'):
            qs = qs.filter(timestamp__date__gte=cd['date_from'])
        if cd.get('date_to'):
            qs = qs.filter(timestamp__date__lte=cd['date_to'])
        if cd.get('username'):
            qs = qs.filter(username__icontains=cd['username'])
        if cd.get('resource'):
            qs = qs.filter(resource__icontains=cd['resource'])
        if cd.get('action'):
            qs = qs.filter(action=cd['action'])
        if cd.get('status') == 'granted':
            qs = qs.filter(success=True)
        elif cd.get('status') == 'denied':
            qs = qs.filter(success=False)

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))
    return render(request, 'accounts/logs/access_logs.html', {'page_obj': page_obj, 'form': form})


@login_required
@require_permission('Violation Reports', 'VIEW')
def violation_logs(request):
    qs   = ViolationLog.objects.select_related('user', 'resolved_by').all()
    form = ViolationFilterForm(request.GET or None)
    if form.is_valid():
        cd = form.cleaned_data
        if cd.get('date_from'):
            qs = qs.filter(timestamp__date__gte=cd['date_from'])
        if cd.get('date_to'):
            qs = qs.filter(timestamp__date__lte=cd['date_to'])
        if cd.get('username'):
            qs = qs.filter(username__icontains=cd['username'])
        if cd.get('severity'):
            qs = qs.filter(severity=cd['severity'])
        if cd.get('status') == 'open':
            qs = qs.filter(is_resolved=False)
        elif cd.get('status') == 'resolved':
            qs = qs.filter(is_resolved=True)

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))
    return render(request, 'accounts/logs/violations.html', {'page_obj': page_obj, 'form': form})


@login_required
@require_permission('Violation Reports', 'EDIT')
def resolve_violation(request, pk):
    violation = get_object_or_404(ViolationLog, pk=pk)
    if violation.is_resolved:
        messages.info(request, 'This violation is already resolved.')
        return redirect('accounts:violation_logs')
    form = ResolveViolationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        violation.resolve(request.user, form.cleaned_data['resolution_note'])
        messages.success(request, f'Violation #{violation.pk} marked as resolved.')
        return redirect('accounts:violation_logs')
    return render(request, 'accounts/logs/resolve.html', {'violation': violation, 'form': form})


# ─── Export / Reports ──────────────────────────────────────────────────────

@login_required
@require_permission('Access Logs', 'EXPORT')
def export_access_logs(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="access_logs.csv"'
    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Username', 'Resource', 'Action', 'Status', 'IP Address', 'Reason'])
    for log in AccessLog.objects.all():
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.username, log.resource, log.action,
            'GRANTED' if log.success else 'DENIED',
            log.ip_address or '', log.reason,
        ])
    return response


@login_required
@require_permission('Violation Reports', 'EXPORT')
def export_violation_logs(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="violation_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Username', 'Resource', 'Attempted Action',
                     'Severity', 'Status', 'IP Address', 'Description',
                     'Resolved By', 'Resolved At', 'Resolution Note'])
    for v in ViolationLog.objects.all():
        writer.writerow([
            v.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            v.username, v.resource, v.attempted_action, v.severity,
            'Resolved' if v.is_resolved else 'Open',
            v.ip_address or '', v.description,
            v.resolved_by.username if v.resolved_by else '',
            v.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if v.resolved_at else '',
            v.resolution_note,
        ])
    return response


@login_required
@require_permission('Access Logs', 'VIEW')
def reports(request):
    today = timezone.now().date()
    # Top resources accessed
    top_resources = (AccessLog.objects
                     .values('resource')
                     .annotate(count=Count('id'))
                     .order_by('-count')[:10])
    # Top violators
    top_violators = (ViolationLog.objects
                     .values('username')
                     .annotate(count=Count('id'))
                     .order_by('-count')[:10])
    # Severity breakdown
    severity_data = {s: ViolationLog.objects.filter(severity=s).count()
                     for s, _ in [('LOW',''), ('MEDIUM',''), ('HIGH',''), ('CRITICAL','')]}
    # Monthly access trend
    monthly = []
    for i in range(5, -1, -1):
        from datetime import date
        import calendar
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12; y -= 1
        _, last_day = calendar.monthrange(y, m)
        start = date(y, m, 1); end = date(y, m, last_day)
        total  = AccessLog.objects.filter(timestamp__date__range=[start, end]).count()
        denied = AccessLog.objects.filter(timestamp__date__range=[start, end], success=False).count()
        monthly.append({'label': date(y, m, 1).strftime('%b %Y'), 'total': total, 'denied': denied})

    return render(request, 'accounts/reports.html', {
        'top_resources': top_resources, 'top_violators': top_violators,
        'severity_data': severity_data, 'monthly': monthly,
        'severity_json': json.dumps(severity_data),
        'monthly_labels': json.dumps([m['label'] for m in monthly]),
        'monthly_total':  json.dumps([m['total'] for m in monthly]),
        'monthly_denied': json.dumps([m['denied'] for m in monthly]),
    })


# ─── User Profile ──────────────────────────────────────────────────────────

@login_required
def my_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    my_logs = AccessLog.objects.filter(user=request.user)[:15]
    return render(request, 'accounts/profile.html', {'profile': profile, 'my_logs': my_logs})


# ─── Helpers ───────────────────────────────────────────────────────────────

def _get_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')


def _roles_grouped():
    """Return Role queryset (used in user forms)."""
    return Role.objects.filter(is_active=True)
