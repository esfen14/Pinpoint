## 6. Troubleshooting and FAQ

### 6.1 Common problems and solutions

| Problem | Likely cause | What to do |
|---|---|---|
| Cannot reach the sign-in page | Wrong address, or your computer is not on the right network | Check the address with your administrator; try from a computer on the office network |
| "Account inactive." | The account is Inactive | Ask an administrator to set it Active |
| "This account is suspended. Contact the admin for any concerns." | The account is Suspended | Ask an administrator to set it Active |
| "Your session expired due to inactivity. Please log in again." | Idle longer than the session timeout | Sign in again |
| "You are already signed in…" | A sign-in page was left open and this browser has since signed in | Sign out first, then sign in |
| A page is missing from the sidebar | Your role lacks the permission | Ask an administrator |
| Dashboard shows old data | Nagios stopped, or PinPoint polling stopped | Read **Data Updated** and **Monitoring System** in the Service Overview panel; if Nagios is stopped, tell the administrator (Technical Manual, section 11) |
| A device is missing from counts | It is paused, retired or merged | Change the Device Inventory **Monitoring** filter to find it |
| A port is not monitored | Its plugin is off, or the port is ignored or held | Open the device's Ports section and read the reason |
| "Not configured" | No check supplies that value | Enable the plugin in Plugin Manager or add the NCPA metric |
| CPU, memory and disk show no value, or the Dashboard CPU chart is missing | No host has the NCPA agent | Deploy NCPA ([NCPA deployment](guides/NCPA_Deployment.md)) |
| No alert email arrives | Email not set up, account not opted in, quiet hours, or maintenance | Check **Settings → Email**, the account's Email Alerts, the notification policy and maintenance windows |
| **Check now** refused | Same target checked under 10 seconds ago, or device paused | Wait and retry; resume the device |
| A scan finds nothing | The network is not listed, or the range is wrong | Check **Settings → Network Discovery** |

### 6.2 Frequently asked questions

**Does acknowledging an alert fix it?**
No. It records that someone is handling it.

**Can I delete a user?**
No. Set the account Inactive or Suspended; its history is kept.

**Why does a device show UNREACHABLE instead of DOWN?**
Its parent device is down, so Nagios cannot tell whether the device itself
is down.

**Is the data live?**
Nearly. Nagios checks every few minutes (default 5), PinPoint reads the
results (default every 60 seconds) and your browser refreshes at your chosen
rate.

**Does PinPoint send data to the internet?**
No monitoring data leaves the server, except the email you configure: alerts, and
notices to a user whose password, email or role an administrator changed.

**Can I see Nagios's own pages?**
Not as an operator; PinPoint replaces them.

### 6.3 When and how to contact support

Contact your PinPoint administrator when:

- Nagios shows as stopped, or data stays old after a refresh;
- you need a permission or a new account;
- you suspect someone else is using your account;
- a change in Settings fails with an error you do not understand.

Give them: the page address, the time, what you did, and the exact message on
screen.

If your administrator cannot resolve it, they can contact one of the people who
built PinPoint and its installer: **Lorraine, Rafael or Elle**. Their time is
limited while they are on on-the-job training (OJT), so expect delays. Personal
contact details are not published in this manual.
