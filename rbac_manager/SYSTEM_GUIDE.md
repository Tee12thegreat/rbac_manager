# RBAC Manager — Beginner's System Guide

This guide explains what the RBAC Manager is, how it works, and how to use every part of it. No prior experience with security systems is needed.

---

## What is RBAC?

**Role-Based Access Control (RBAC)** is a way of controlling who can do what inside a system.

Instead of giving each user their own individual set of permissions (which gets unmanageable fast), you create **roles** — like "HR Manager" or "Finance Approver" — and attach permissions to those roles. You then assign roles to users. A user's access is automatically determined by the roles they hold.

### Key terms

| Term | What it means |
|------|--------------|
| **User** | A person who logs into the system |
| **Role** | A job function, like "IT Admin" or "Auditor" |
| **Resource** | Something that can be accessed, like "Payroll", "User Accounts", or "Reports" |
| **Permission** | The ability to perform one action on one resource, e.g. "VIEW Employee Records" |
| **Access Log** | A record of every time someone tried to access something |
| **Violation** | A record of an access that was denied because the user lacked permission |

---

## What is Least Privilege?

**Least Privilege** means every user should only have the minimum permissions they need to do their job — nothing more.

For example, a receptionist might only need to VIEW the appointment calendar. They should not be able to EDIT payroll records. The RBAC Manager enforces this automatically: if a user tries to access something they don't have permission for, they are blocked and a violation record is created.

---

## What is Segregation of Duties (SoD)?

**Segregation of Duties** is the principle that no single person should have control over an entire sensitive process.

Classic example: the person who authorises payments should not be the same person who processes them. This reduces the risk of fraud.

In this system, you can mark two roles as **incompatible**. If a user is assigned one role, the system will refuse to also assign them the incompatible role. For example:

- `Finance Manager` is incompatible with `Finance Approver`
- `IT Admin` is incompatible with `Auditor`

---

## How to Use the System

### Logging In

1. Open your browser and go to **http://127.0.0.1:8000/**
2. You will be redirected to the login page.
3. Enter your username and password, then click **Log In**.
4. You will land on the Dashboard.

> Demo accounts are listed in the README. Try `superadmin / Admin@1234` for full access.

---

### The Dashboard

The dashboard gives you an at-a-glance view of the system:

- **Total Users** — how many user accounts exist
- **Total Roles** — how many roles are defined
- **Total Resources** — how many protected resources exist
- **Open Violations** — access attempts that were denied and have not yet been reviewed
- **Today's Access** — number of access events today
- **Today's Denied** — how many were blocked today

Below the cards you'll find:
- A **bar chart** showing granted vs denied access over the past 7 days
- A **doughnut chart** showing how many users are in each role
- A table of the **10 most recent access events**
- A table of **open violations** that need attention

---

### Managing Users

**Where:** Sidebar → Administration → Users

**What you can do:**
- **List Users** — see all users, their department, roles, and status
- **Add User** — create a new user, assign them a department and roles
- **Edit User** — update a user's details or change their roles. You can also set a new password here.
- **View User** — see a full breakdown of a user's permissions and recent activity
- **Delete User** — permanently remove a user

> When creating or editing a user, the system automatically checks for SoD conflicts. If you try to assign two incompatible roles, you will see an error.

---

### Managing Roles

**Where:** Sidebar → Administration → Roles

**What you can do:**
- **List Roles** — see all roles, how many permissions they have, and how many users hold each role
- **Create Role** — define a new role, select which permissions it grants, and mark any roles it conflicts with (SoD)
- **Edit Role** — update permissions or SoD constraints
- **Delete Role** — only possible if no users currently hold the role

> In the role form, permissions are grouped by resource. Use the "Toggle All" button to quickly grant or revoke all permissions for a resource.

---

### Managing Resources

**Where:** Sidebar → Administration → Resources

A **Resource** represents something that can be protected — a screen, a data set, a report, or any module of the system.

**What you can do:**
- **List Resources** — see all resources and their defined actions
- **Create Resource** — give it a name, a module category, and select which actions are allowed (VIEW, CREATE, EDIT, DELETE, EXPORT, APPROVE)

> When you create a resource and select actions, the system automatically creates a Permission entry for each action. These permissions can then be assigned to roles.

---

### Viewing Access Logs

**Where:** Sidebar → Audit & Compliance → Access Logs

Every time someone successfully accesses a resource — or is blocked from doing so — the event is recorded here.

**Each record shows:**
- When it happened (timestamp)
- Who tried to access it (username)
- What they tried to access (resource and action)
- Their IP address
- Whether access was **Granted** (green) or **Denied** (red)
- The reason (e.g. "Permission granted", "Insufficient permissions")

**Filtering:** Use the filter panel at the top to narrow results by date, username, resource, action, or status.

**Exporting:** Click the **Export CSV** button to download the filtered log as a spreadsheet.

---

### Viewing Violations

**Where:** Sidebar → Audit & Compliance → Violations

A violation is created automatically any time access is denied. Violations are given a **severity** rating:

| Severity | When it's assigned |
|----------|-------------------|
| **LOW** | The user had VIEW access but tried a write action (CREATE/EDIT/DELETE) |
| **MEDIUM** | Standard denied access |
| **HIGH** | The user has no roles at all |
| **CRITICAL** | The user triggered 3 or more denied access attempts within 10 minutes |

**Resolving a violation:**
1. Find the violation in the list.
2. Click the green **✓** (resolve) button on the right.
3. On the next screen, review the violation details.
4. Write a resolution note (e.g. "User error — no malicious intent", "Access policy updated").
5. Click **Mark as Resolved**.

Resolved violations remain in the log for audit purposes but are no longer counted as open.

---

### Reports

**Where:** Sidebar → Audit & Compliance → Reports

The Reports page gives a visual summary of system activity:

- **6-Month Access Trend** — line chart of total vs denied access per month
- **Violations by Severity** — doughnut chart breaking down LOW / MEDIUM / HIGH / CRITICAL
- **Most Accessed Resources** — which resources are accessed most often
- **Top Violators** — which users have triggered the most violations

---

### My Profile

**Where:** Click your username in the sidebar footer, or Sidebar → My Profile

This page shows your own user information:
- Your name, department, employee ID, and email
- Your assigned roles
- All permissions you currently have (from all your roles combined)
- Your 15 most recent access events

---

## Security Notes

- **Passwords** should be changed from the demo defaults before any real use.
- The **superadmin** account bypasses all permission checks — restrict access to it.
- Access logs are append-only from the user interface — they cannot be deleted through the app.
- Violations with **CRITICAL** severity should be investigated promptly, as they may indicate a brute-force or probing attempt.

---

## Frequently Asked Questions

**Q: A user says they can't access a page they should be able to. What do I do?**
A: Go to Administration → Users, find the user, and click View. Check their roles and the permissions those roles grant. If the required permission is missing, either add it to their role (Administration → Roles → Edit) or assign them an appropriate role.

**Q: How do I reset a user's password?**
A: Go to Administration → Users → Edit User. Scroll to the "New Password" field, enter the new password, and save.

**Q: Can I create a role with no permissions?**
A: Yes, but it won't grant the user any additional access.

**Q: Why can't I delete a role?**
A: A role can only be deleted when no users hold it. Go to the user list, remove the role from any users who have it, then try deleting again.

**Q: What does it mean when a violation says "3+ violations in 10 minutes"?**
A: This is a CRITICAL violation — the user triggered multiple denied access attempts in quick succession. This could be accidental (a bug or misconfiguration) or deliberate (someone probing for access they don't have). Investigate and resolve accordingly.
