from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Auth
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard & Profile
    path('dashboard/', views.dashboard,  name='dashboard'),
    path('profile/',   views.my_profile, name='my_profile'),

    # Users
    path('users/',                  views.user_list,   name='user_list'),
    path('users/create/',           views.user_create, name='user_create'),
    path('users/<int:pk>/',         views.user_detail, name='user_detail'),
    path('users/<int:pk>/edit/',    views.user_edit,   name='user_edit'),
    path('users/<int:pk>/delete/',  views.user_delete, name='user_delete'),

    # Roles
    path('roles/',                  views.role_list,   name='role_list'),
    path('roles/create/',           views.role_create, name='role_create'),
    path('roles/<int:pk>/edit/',    views.role_edit,   name='role_edit'),
    path('roles/<int:pk>/delete/',  views.role_delete, name='role_delete'),

    # Resources
    path('resources/',          views.resource_list,   name='resource_list'),
    path('resources/create/',   views.resource_create, name='resource_create'),

    # Logs
    path('logs/access/',                         views.access_logs,       name='access_logs'),
    path('logs/violations/',                     views.violation_logs,    name='violation_logs'),
    path('logs/violations/<int:pk>/resolve/',    views.resolve_violation, name='resolve_violation'),

    # Reports & Exports
    path('reports/',                  views.reports,               name='reports'),
    path('reports/export/access/',    views.export_access_logs,    name='export_access_logs'),
    path('reports/export/violations/',views.export_violation_logs, name='export_violation_logs'),
]
