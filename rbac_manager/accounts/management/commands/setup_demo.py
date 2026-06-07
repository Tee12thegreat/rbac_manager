from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Department, Resource, Permission, Role, UserProfile


class Command(BaseCommand):
    help = 'Populate the database with demo roles, resources, and users.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Setting up demo data...'))

        # ── Departments ────────────────────────────────────────────────
        dept_data = [
            ('IT',         'Information Technology'),
            ('Finance',    'Finance and Accounting'),
            ('HR',         'Human Resources'),
            ('Operations', 'Operations'),
            ('Audit',      'Internal Audit & Compliance'),
            ('Management', 'Senior Management'),
        ]
        depts = {}
        for name, desc in dept_data:
            d, _ = Department.objects.get_or_create(name=name, defaults={'description': desc})
            depts[name] = d

        # ── Resources & Permissions ────────────────────────────────────
        res_data = [
            ('User Management',    'Administration', ['VIEW','CREATE','EDIT','DELETE']),
            ('Role Management',    'Administration', ['VIEW','CREATE','EDIT','DELETE']),
            ('Resource Management','Administration', ['VIEW','CREATE','EDIT','DELETE']),
            ('Employee Records',   'HR',             ['VIEW','CREATE','EDIT','DELETE','EXPORT']),
            ('Financial Records',  'Finance',        ['VIEW','CREATE','EDIT','DELETE','EXPORT','APPROVE']),
            ('Access Logs',        'Audit',          ['VIEW','EXPORT']),
            ('Violation Reports',  'Audit',          ['VIEW','EDIT','EXPORT']),
            ('System Settings',    'Administration', ['VIEW','EDIT']),
        ]
        resources = {}
        perms     = {}  # perms[res_name][action] = Permission obj
        for rname, module, actions in res_data:
            res, _ = Resource.objects.get_or_create(name=rname, defaults={'module': module})
            resources[rname] = res
            perms[rname] = {}
            for action in actions:
                p, _ = Permission.objects.get_or_create(resource=res, action=action)
                perms[rname][action] = p

        # ── Roles ──────────────────────────────────────────────────────
        def make_perms(spec):
            """spec = {resource_name: [action, ...]}"""
            result = []
            for rname, actions in spec.items():
                for act in actions:
                    if rname in perms and act in perms[rname]:
                        result.append(perms[rname][act])
            return result

        roles_spec = {
            'Super Admin': {
                r: list(a.keys()) for r, a in perms.items()
            },
            'IT Admin': {
                'User Management':    ['VIEW','CREATE','EDIT','DELETE'],
                'Role Management':    ['VIEW','CREATE','EDIT','DELETE'],
                'Resource Management':['VIEW','CREATE','EDIT'],
                'Access Logs':        ['VIEW'],
                'System Settings':    ['VIEW','EDIT'],
            },
            'HR Manager': {
                'Employee Records': ['VIEW','CREATE','EDIT','EXPORT'],
                'User Management':  ['VIEW'],
            },
            'Finance Manager': {
                'Financial Records': ['VIEW','CREATE','EDIT','EXPORT'],
                'Employee Records':  ['VIEW'],
            },
            'Finance Approver': {
                'Financial Records': ['VIEW','APPROVE'],
            },
            'Auditor': {
                'Access Logs':       ['VIEW','EXPORT'],
                'Violation Reports': ['VIEW','EDIT','EXPORT'],
                'User Management':   ['VIEW'],
                'Role Management':   ['VIEW'],
                'Employee Records':  ['VIEW'],
                'Financial Records': ['VIEW'],
            },
            'Employee': {},
        }

        role_objs = {}
        descs = {
            'Super Admin':      'Full system access – break-glass account.',
            'IT Admin':         'Manages users, roles, and system configuration.',
            'HR Manager':       'Manages employee records and HR data.',
            'Finance Manager':  'Creates and manages financial records.',
            'Finance Approver': 'Approves financial records only (cannot create – SoD).',
            'Auditor':          'Read-only access to logs, violations, and records.',
            'Employee':         'Standard employee with minimal access.',
        }
        for rname, spec in roles_spec.items():
            role, _ = Role.objects.get_or_create(name=rname, defaults={'description': descs.get(rname, '')})
            role.permissions.set(make_perms(spec))
            role_objs[rname] = role

        # ── Segregation of Duties ──────────────────────────────────────
        # IT Admin <-> Auditor (those who maintain logs cannot audit them)
        role_objs['IT Admin'].incompatible_roles.add(role_objs['Auditor'])
        # Finance Manager <-> Finance Approver (creator != approver)
        role_objs['Finance Manager'].incompatible_roles.add(role_objs['Finance Approver'])

        # ── Users ──────────────────────────────────────────────────────
        users_data = [
            dict(username='superadmin',  password='Admin@1234',    fn='System',   ln='Administrator',
                 email='superadmin@rbac.local',  role='Super Admin',     dept='IT',
                 emp_id='EMP001', is_staff=True, is_superuser=True),
            dict(username='itadmin',     password='ITAdmin@123',   fn='John',     ln='Mwangi',
                 email='itadmin@rbac.local',     role='IT Admin',        dept='IT',         emp_id='EMP002'),
            dict(username='hrmanager',   password='HRMgr@123',     fn='Tendai',   ln='Chikwanda',
                 email='hrmanager@rbac.local',   role='HR Manager',      dept='HR',         emp_id='EMP003'),
            dict(username='finmanager',  password='FinMgr@123',    fn='Blessing', ln='Moyo',
                 email='finmanager@rbac.local',  role='Finance Manager', dept='Finance',    emp_id='EMP004'),
            dict(username='finapprov',   password='FinApp@123',    fn='Chiedza',  ln='Mutasa',
                 email='finapprov@rbac.local',   role='Finance Approver',dept='Finance',    emp_id='EMP005'),
            dict(username='auditor',     password='Audit@123',     fn='Rumbi',    ln='Ncube',
                 email='auditor@rbac.local',     role='Auditor',         dept='Audit',      emp_id='EMP006'),
            dict(username='employee1',   password='Emp@12345',     fn='Tapiwa',   ln='Dube',
                 email='employee1@rbac.local',   role='Employee',        dept='Operations', emp_id='EMP007'),
        ]

        for ud in users_data:
            user, created = User.objects.get_or_create(
                username=ud['username'],
                defaults=dict(
                    first_name=ud['fn'], last_name=ud['ln'], email=ud['email'],
                    is_staff=ud.get('is_staff', False),
                    is_superuser=ud.get('is_superuser', False),
                )
            )
            if created:
                user.set_password(ud['password'])
                user.save()

            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults=dict(department=depts.get(ud['dept']), employee_id=ud['emp_id'])
            )
            role = role_objs.get(ud['role'])
            if role:
                profile.roles.set([role])

            self.stdout.write(f"  {'Created' if created else 'Exists '}: {ud['username']} / {ud['password']}  [{ud['role']}]")

        self.stdout.write(self.style.SUCCESS('\nDemo data ready! Login credentials above.'))
