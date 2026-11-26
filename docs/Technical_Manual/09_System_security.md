## 9. System security

### 9.1 Authentication and authorization

- Session-cookie authentication (Flask-Login); a second login in the same
  session is refused (409).
- Every data route uses `@login_required` and
  `@require_permission("<name>")`; the client guard is only usability.
- Session timeout 15–240 minutes (Settings → Security).
- Bootstrap administrator must complete setup; protected from losing
  account/role administration.

### 9.2 Role-based access control

Roles hold permissions (list in User Manual 5.2 and
[`Backend_Modules_and_Routes.md`](../../spec%20files/Backend_Modules_and_Routes.md)).
`Super Admin` has an immutable full set. New permissions are added by
`flask sync-permissions`.

### 9.3 Password protection

Strong policy option (12+ characters with four classes); reuse of the current
password refused; forced change after admin reset. Password recovery is
administrator-mediated (no email reset).

### 9.4 Encryption and secure communication

| Path | Protection |
|---|---|
| Browser ↔ PinPoint | HTTP on port 80, in the lab and as installed (the installer configures no HTTPS). **[R]** Enable TLS in Nginx with an internal CA or Let's Encrypt and set secure cookie flags |
| PinPoint ↔ SMTP | STARTTLS required (Gmail or custom relay) |
| PinPoint ↔ NCPA | NCPA HTTPS API with token |
| PinPoint ↔ devices (SSH) | Pinned host-key fingerprint, explicit trust |
| Secrets at rest | Fernet encryption in `system.db`; protected Nagios resource file |

### 9.5 Firewall and network protection

See 5.7. Nagios web and Gunicorn listen on loopback.

### 9.6 Data privacy

Monitoring data stays on the appliance. Personal data held: account names and
emails, activity logs. Secrets are never returned by the API or logged; Nagios
log view redacts command text and plugin output.

### 9.7 Security logging and monitoring

Activity, configuration, discovery, NCPA and export logs; failed-login
monitoring and audit logging toggles; plugin security validation on a
schedule.

### 9.8 Vulnerability management

Pinned dependencies; CI runs on every pull request. **[R]** Add dependency
scanning (`pip-audit`, `npm audit`) and OS unattended security updates.

### 9.9 Known security gaps and recommendations

| Item | Status | Recommendation |
|---|---|---|
| HTTPS | Not configured by the installer | **[R]** TLS on Nginx, HSTS, secure cookies |
| SNMPv3 passphrases in `check_snmp` child argv | Known gap | **[R]** Replace the v3 client with one reading a protected file |
| Narrower `nagios` group rights for event handlers | Open installer item | Complete in installer |
| No account lockout or login rate limiting; failed logins are only recorded in the activity log when Failed Login Monitoring is on (`api/user/login.py`) | Gap | **[R]** Add rate limiting in Nginx or the app |
| Backups not copied off the host | By design | **[R]** Encrypted off-host copy |
