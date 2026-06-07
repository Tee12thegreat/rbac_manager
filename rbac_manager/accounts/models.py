from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

ACTION_CHOICES = [
    ('VIEW',    'View'),
    ('CREATE',  'Create'),
    ('EDIT',    'Edit'),
    ('DELETE',  'Delete'),
    ('EXPORT',  'Export'),
    ('APPROVE', 'Approve'),
]

SEVERITY_CHOICES = [
    ('LOW',      'Low'),
    ('MEDIUM',   'Medium'),
    ('HIGH',     'High'),
    ('CRITICAL', 'Critical'),
]

class Department(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['name']
    def __str__(self):
        return self.name

class Resource(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    module      = models.CharField(max_length=100, default='General')
    created_at  = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['module', 'name']
    def __str__(self):
        return self.name

class Permission(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='permissions')
    action   = models.CharField(max_length=20, choices=ACTION_CHOICES)
    class Meta:
        unique_together = ['resource', 'action']
        ordering        = ['resource', 'action']
    def __str__(self):
        return f"{self.action} – {self.resource.name}"

class Role(models.Model):
    name               = models.CharField(max_length=100, unique=True)
    description        = models.TextField(blank=True)
    permissions        = models.ManyToManyField(Permission, blank=True, related_name='roles')
    incompatible_roles = models.ManyToManyField('self', blank=True, symmetrical=True)
    is_active          = models.BooleanField(default=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['name']
    def __str__(self):
        return self.name
    def permission_count(self):
        return self.permissions.count()

class UserProfile(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    roles       = models.ManyToManyField(Role, blank=True, related_name='members')
    department  = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    phone       = models.CharField(max_length=20, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['user__username']
    def __str__(self):
        name = self.user.get_full_name()
        return name if name else self.user.username
    def has_permission(self, resource_name, action):
        return self.roles.filter(
            is_active=True,
            permissions__resource__name=resource_name,
            permissions__action=action,
        ).exists()
    def get_all_permissions(self):
        perms = set()
        for role in self.roles.filter(is_active=True):
            for perm in role.permissions.select_related('resource'):
                perms.add(f"{perm.action}_{perm.resource.name}")
        return perms
    def check_sod_violations(self, new_roles):
        violations = []
        role_list = list(new_roles)
        for i, role_a in enumerate(role_list):
            for role_b in role_list[i + 1:]:
                if role_b in role_a.incompatible_roles.all():
                    violations.append(
                        f'"{role_a.name}" and "{role_b.name}" cannot be assigned together (SoD conflict).'
                    )
        return violations

class AccessLog(models.Model):
    user       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='access_logs')
    username   = models.CharField(max_length=150)
    resource   = models.CharField(max_length=200)
    action     = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp  = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    success    = models.BooleanField(default=True)
    reason     = models.TextField(blank=True)
    class Meta:
        ordering = ['-timestamp']
    def __str__(self):
        status = 'GRANTED' if self.success else 'DENIED'
        return f"[{status}] {self.username} -> {self.action} {self.resource}"

class ViolationLog(models.Model):
    user             = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='violations')
    username         = models.CharField(max_length=150)
    resource         = models.CharField(max_length=200)
    attempted_action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp        = models.DateTimeField(auto_now_add=True)
    ip_address       = models.GenericIPAddressField(null=True, blank=True)
    severity         = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    description      = models.TextField(blank=True)
    is_resolved      = models.BooleanField(default=False)
    resolved_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_violations')
    resolved_at      = models.DateTimeField(null=True, blank=True)
    resolution_note  = models.TextField(blank=True)
    class Meta:
        ordering = ['-timestamp']
    def __str__(self):
        status = 'Resolved' if self.is_resolved else 'Open'
        return f"[{self.severity}|{status}] {self.username} -> {self.attempted_action} {self.resource}"
    def resolve(self, resolved_by_user, note=''):
        self.is_resolved    = True
        self.resolved_by    = resolved_by_user
        self.resolved_at    = timezone.now()
        self.resolution_note = note
        self.save()
