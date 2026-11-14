# Sign in, accounts and roles

This guide covers signing in and out, the first-run setup window, forgotten passwords, and the **Manage Accounts** and **Manage Roles** pages for administrators.

> **Verification status.** Written on 2026-11-14 from the route specification (`spec files/Frontend_Modules_and_Routes.md`, `Backend_Modules_and_Routes.md`) and the source. It has not yet been followed step by step on a demo build; items marked **TBC** need that check, and screenshots are not included yet.

## Purpose

Pinpoint shows each person only the pages their role allows. An account has one role; a role is a named set of permissions. Sign in with your own account, and ask an administrator if a page you need is missing from the sidebar.

## Prerequisites

- A Pinpoint account created by an administrator (there is no self-registration).
- To manage accounts: the **account.view** permission (list), **account.info** (details) and **account.edit** (create, edit, reset passwords).
- To manage roles: **role.view**, **role.info**, **role.edit** and **role.list**.

## Sign in and sign out

1. Open Pinpoint in a browser. Any address that needs you to be signed in sends you to the sign-in page.
2. Enter your **email** and **password**. Optionally choose **Remember me**. **TBC:** what Remember me changes in practice (the session timeout in **Settings → Security** still applies).
3. Choose the sign-in button. You land on the first page your role is allowed to see (normally Dashboard).
4. To switch accounts, sign out first. Signing in while already signed in is refused with "You are already signed in. Sign out before logging in to another account."
5. To leave, use the sign-out control in the header.

Expected result: the sidebar shows only the pages you have permission for.

Precautions:
- A session ends after the idle period set in **Settings → Security → Session Timeout** (15 minutes, 30 minutes, 1, 2 or 4 hours). You are returned to the sign-in page ("Session expired. Please log in again.").
- An account whose status is not **Active** is refused ("Account inactive.").

## First-run setup (new installation)

The first administrator account is created by the installer with a placeholder email ending in `@pinpoint.lan` and a placeholder password. The first sign-in shows a setup window that cannot be skipped:

1. Enter the **current password** (the installer's).
2. Enter your real **new email** (the `pinpoint.lan` placeholder domain is refused) and a **new password** twice.
3. Save. If Pinpoint could not apply the change to Nagios you see a warning, but the account is saved.

If you are locked out of the first account, an operator with server access can run `flask recover-bootstrap-admin`; see [`server/README.md`](../../server/README.md#command-line-commands).

## Change your password

When an administrator creates an account or resets a password, the account is usually flagged **Must change password**. At the next sign-in a blocking window asks for the current password and a new one, entered twice. Until it is done, every other page is refused.

Password rules depend on **Settings → Security → Strong Password Policy**:

| Policy | Rule |
|---|---|
| Off | At least 8 characters |
| On | At least 12 characters, with an uppercase letter, a lowercase letter, a number and a special character |

A new password may not be the account's current password.

## Forgot password

1. On the sign-in page choose **Forgot Password?** and enter your email.
2. Pinpoint always shows the same confirmation, so it cannot be used to find out which emails exist. **No email is sent** and there is no reset link.
3. An administrator sees the request (a bell alert and the **Password reset requests** panel on Manage Accounts), chooses **Reset password**, and sets a new temporary password for you. Give the person the new password through a channel you trust. You must change it at your next sign-in.
4. An administrator can also dismiss a request.

## Manage Accounts (administrators)

Open **Manage Accounts** (`/accounts`). The table lists name, email, role, status, joined date and **Email Alerts** (On/Off), with search, a status filter and sorting.

### Add a user

1. Choose the add-user button.
2. Enter **first name**, **last name**, **email**, a **role** (the first active role is preselected), and a password twice. The password must meet the active password policy.
3. **Require password change at first sign-in** is ticked by default; clear it only if the person should keep the password you chose.
4. **Send this user email alerts** appears only if you hold **account.alerts**. When it is on, the account is added to the Nagios contacts that receive alert email; see [Notification policy](Notification_Policy.md) and [Email settings](Email_Settings.md).
5. Save. The dialog closes and the list refreshes. If the save is rejected the dialog stays open with your entries and the reason.

### Edit an account or change its status

1. Open the account and choose **Edit Account**.
2. Change the name, role or **Status**. The three statuses are **Active**, **Inactive** and **Suspended**; only Active accounts can sign in. Accounts are never deleted, only made inactive or suspended.
3. To set a new password, enter it twice. Entering the account's current password is refused and the dialog stays open.
4. Save.

Protected first account: the first account created (the bootstrap administrator) must stay **Active**, and can only hold an active role that has all seven account and role administration permissions. The edit form disables the status selector for it.

### Answer a password reset request

Open the **Password reset requests** panel, choose **Reset password** for the request, enter a new password twice, and save. The person must change it at next sign-in.

## Manage Roles (administrators)

Open **Manage Roles** (`/manage-roles`).

1. Choose the add-role control. Enter a **Role Name** (for example "Supervisor"), a short **Description**, and tick the **Permissions** the role grants.
2. Save. New roles are active.
3. To change a role, choose **Edit role**, adjust name, description and permissions, and save. Use **Role status** to deactivate a role; an inactive role cannot be given to a new account.

Built-in roles after a fresh install: **Super Admin** (all permissions), **Manager** and **Staff**. **TBC:** the exact permission set of Manager and Staff on a production install (`flask init-production` creates reference data; the development `flask seed` differs).

Precautions:
- **Super Admin** cannot be renamed and its permissions cannot be changed; the page shows every permission as read-only.
- The role of the bootstrap administrator is marked locked: its edit form disables the seven account and role permission controls and deactivation, so the last administrator cannot lose the ability to manage accounts.
- After an upgrade, run `flask sync-permissions` so newly introduced permissions exist and are granted to Super Admin; grant them to other roles here.
- Permission changes apply to people already signed in at their next request to the server **TBC**.

## Permission names used across the guides

| Area | Permissions |
|---|---|
| Accounts | `account.view`, `account.info`, `account.edit`, `account.alerts` |
| Roles | `role.view`, `role.info`, `role.edit`, `role.list` |
| Pages | `system.dashboard`, `system.network_health`, `system.history`, `system.report`, `system.logs`, `maintenance.manage`, `remediation.view`, `remediation.manage`, `plugin.view` |
| Actions | `system.acknowledge_alerts`, `system.recheck`, `system.discover`, `system.hosts`, `system.hosts.edit`, `system.hosts.alerts`, `system.deploy.ncpa`, `plugin.*` |
| Settings tabs | `settings.security`, `settings.system`, `settings.discovery`, `settings.plugins`, `settings.email` |

The Manage Roles screen is the authoritative list for a running system.
