from django.contrib import admin
from .models import Department, Resource, Permission, Role, UserProfile, AccessLog, ViolationLog

admin.site.register(Department)
admin.site.register(Resource)
admin.site.register(Permission)
admin.site.register(Role)
admin.site.register(UserProfile)

@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display  = ['username', 'resource', 'action', 'success', 'timestamp', 'ip_address']
    list_filter   = ['success', 'action']
    search_fields = ['username', 'resource']
    readonly_fields = ['timestamp']

@admin.register(ViolationLog)
class ViolationLogAdmin(admin.ModelAdmin):
    list_display  = ['username', 'resource', 'attempted_action', 'severity', 'is_resolved', 'timestamp']
    list_filter   = ['severity', 'is_resolved']
    search_fields = ['username', 'resource']
    readonly_fields = ['timestamp']

admin.site.site_header = 'RBAC Manager Administration'
admin.site.site_title  = 'RBAC Admin'
