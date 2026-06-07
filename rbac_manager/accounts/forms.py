from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import UserProfile, Role, Resource, Permission, Department


class StyledAuthForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control form-control-lg', 'placeholder': 'Username'})
        self.fields['password'].widget.attrs.update({'class': 'form-control form-control-lg', 'placeholder': 'Password'})


class UserCreateForm(forms.Form):
    username   = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name  = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email      = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password1  = forms.CharField(label='Password', min_length=6,
                                 widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2  = forms.CharField(label='Confirm Password',
                                 widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    employee_id = forms.CharField(max_length=20, required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone       = forms.CharField(max_length=20, required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    department  = forms.ModelChoiceField(queryset=Department.objects.all(), required=False,
                                         widget=forms.Select(attrs={'class': 'form-select'}))
    roles       = forms.ModelMultipleChoiceField(
        queryset=Role.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple, required=False,
    )
    is_active = forms.BooleanField(required=False, initial=True,
                                   widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('password1'), cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Passwords do not match.')
        # SoD check
        roles = cleaned.get('roles', [])
        if roles:
            role_list = list(roles)
            for i, ra in enumerate(role_list):
                for rb in role_list[i + 1:]:
                    if rb in ra.incompatible_roles.all():
                        self.add_error('roles', f'SoD violation: "{ra.name}" and "{rb.name}" cannot be combined.')
        return cleaned


class UserEditForm(forms.Form):
    first_name  = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name   = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email       = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    employee_id = forms.CharField(max_length=20, required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone       = forms.CharField(max_length=20, required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    department  = forms.ModelChoiceField(queryset=Department.objects.all(), required=False,
                                         widget=forms.Select(attrs={'class': 'form-select'}))
    roles       = forms.ModelMultipleChoiceField(
        queryset=Role.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple, required=False,
    )
    is_active   = forms.BooleanField(required=False,
                                     widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    new_password = forms.CharField(label='New Password (leave blank to keep current)',
                                   required=False, min_length=6,
                                   widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned = super().clean()
        roles = cleaned.get('roles', [])
        if roles:
            role_list = list(roles)
            for i, ra in enumerate(role_list):
                for rb in role_list[i + 1:]:
                    if rb in ra.incompatible_roles.all():
                        self.add_error('roles', f'SoD violation: "{ra.name}" and "{rb.name}" cannot be combined.')
        return cleaned


class RoleForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.select_related('resource').all(),
        widget=forms.CheckboxSelectMultiple, required=False,
    )
    incompatible_roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple, required=False,
        label='Incompatible Roles (SoD Enforcement)',
        help_text='Users will not be allowed to hold both roles simultaneously.',
    )

    class Meta:
        model  = Role
        fields = ['name', 'description', 'is_active', 'permissions', 'incompatible_roles']
        widgets = {
            'name':        forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        # Exclude self from incompatible choices when editing
        if instance:
            self.fields['incompatible_roles'].queryset = Role.objects.exclude(pk=instance.pk)


class ResourceForm(forms.ModelForm):
    actions = forms.MultipleChoiceField(
        choices=[('VIEW','View'),('CREATE','Create'),('EDIT','Edit'),
                 ('DELETE','Delete'),('EXPORT','Export'),('APPROVE','Approve')],
        widget=forms.CheckboxSelectMultiple, required=True,
        label='Allowed Actions',
        help_text='Select all actions that should exist for this resource.',
    )

    class Meta:
        model  = Resource
        fields = ['name', 'description', 'module']
        widgets = {
            'name':        forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'module':      forms.TextInput(attrs={'class': 'form-control'}),
        }


class AccessLogFilterForm(forms.Form):
    date_from = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date'}))
    date_to   = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date'}))
    username  = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Filter by username'}))
    resource  = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Filter by resource'}))
    action    = forms.ChoiceField(required=False,
        choices=[('', 'All Actions')] + [('VIEW','View'),('CREATE','Create'),
                 ('EDIT','Edit'),('DELETE','Delete'),('EXPORT','Export'),('APPROVE','Approve')],
        widget=forms.Select(attrs={'class': 'form-select'}))
    status    = forms.ChoiceField(required=False,
        choices=[('', 'All'), ('granted', 'Granted'), ('denied', 'Denied')],
        widget=forms.Select(attrs={'class': 'form-select'}))


class ViolationFilterForm(forms.Form):
    date_from = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date'}))
    date_to   = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date'}))
    username  = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Filter by username'}))
    severity  = forms.ChoiceField(required=False,
        choices=[('', 'All Severities'), ('LOW','Low'), ('MEDIUM','Medium'),
                 ('HIGH','High'), ('CRITICAL','Critical')],
        widget=forms.Select(attrs={'class': 'form-select'}))
    status    = forms.ChoiceField(required=False,
        choices=[('', 'All'), ('open', 'Open'), ('resolved', 'Resolved')],
        widget=forms.Select(attrs={'class': 'form-select'}))


class ResolveViolationForm(forms.Form):
    resolution_note = forms.CharField(
        label='Resolution Note',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                     'placeholder': 'Describe how this violation was addressed...'}),
        required=True,
    )
