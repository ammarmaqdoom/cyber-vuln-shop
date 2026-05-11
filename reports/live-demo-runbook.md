# Live Demo Runbook

Use this order during the presentation to satisfy the rubric items: live app, live attack, fix proof, and pipeline trigger.

## 1. Start Both App Versions

Terminal 1, fixed app:

```powershell
py -3 seed.py
py -3 app.py
```

Terminal 2, vulnerable app:

```powershell
py -3 demo/vulnerable_app.py
```

Open:

- Fixed app: `http://127.0.0.1:5000`
- Vulnerable app: `http://127.0.0.1:5001`

For graded HTTPS demo, use Docker Compose/Nginx from the installation manual. The local two-port setup is for clear attack/fix proof.

## 2. Live Attack 1: Broken RBAC

### Vulnerable Proof

1. Open `http://127.0.0.1:5001/auth/login`.
2. Log in as `alice` / `Alice1234!`.
3. Browse to `http://127.0.0.1:5001/admin`.
4. Show that `alice` can see the vulnerable admin dashboard and user data.
5. Screenshot name: `rbac-01-vulnerable-alice-admin.png`.

### Fix Proof

1. Open `http://127.0.0.1:5000/auth/login`.
2. Log in as `alice` / `Alice1234!`.
3. Browse to `http://127.0.0.1:5000/admin`.
4. Show that the fixed app redirects away from admin.
5. Log in as `admin` / `Admin1234!`.
6. Show that admin can access `http://127.0.0.1:5000/admin`.
7. Screenshot names:
   - `rbac-02-fixed-alice-denied.png`
   - `rbac-03-fixed-admin-allowed.png`

Presentation line:

> This is a broken access control issue. The vulnerable version only checked whether the user was logged in, while the fixed version checks the admin role before serving admin routes.

## 3. Live Attack 2: CSRF Profile Update

### Vulnerable Proof

1. Keep `alice` logged in on `http://127.0.0.1:5001`.
2. Open `demo/csrf_attack_vulnerable.html` in the browser.
3. It auto-submits a forged POST to `http://127.0.0.1:5001/profile/update`.
4. Open `http://127.0.0.1:5001/profile`.
5. Show username changed to `csrf_owned_user`.
6. Screenshot name: `csrf-01-vulnerable-profile-changed.png`.

### Fix Proof

1. Keep `alice` logged in on `http://127.0.0.1:5000`.
2. Open `demo/csrf_attack_fixed.html`.
3. Show that the fixed app rejects the forged POST because no CSRF token is present.
4. Screenshot name: `csrf-02-fixed-forbidden.png`.

Presentation line:

> This is CSRF. The vulnerable app trusted any POST from the browser. The fixed app requires a valid server-generated CSRF token on every state-changing form.

## 3b. Live Attack: SQL Injection On Product Search

### Vulnerable Proof

1. Log in as `alice` on the vulnerable build.
2. Open `http://127.0.0.1:5001/products/?q=%25%27%20UNION%20SELECT%20id%2C%20email%2C%20%27%27%2C%200%2C%200%2C%20%27%27%2C%20%27%27%20FROM%20users--`.
3. Show that emails such as `alice@example.com` and `admin@vulnshop.local` appear as product names.
4. Screenshot name: `sqli-01-vulnerable-email-leak.png`.

### Fix Proof

1. Repeat the same URL against `http://127.0.0.1:5000/products/?q=...`.
2. Show that the catalog page lists no leaked emails.
3. Screenshot name: `sqli-02-fixed-no-leak.png`.

## 3c. Live Attack: Stored XSS In Reviews

### Vulnerable Proof

1. Log in as `alice` on the vulnerable build.
2. Open `http://127.0.0.1:5001/products/1`.
3. Post a review with the text `<script>alert('xss')</script>`.
4. Refresh the product page and show the raw `<script>` element in the rendered HTML.
5. Screenshot name: `xss-01-vulnerable-script-tag.png`.

### Fix Proof

1. Log in as `bob` on the fixed build.
2. Open `http://127.0.0.1:5000/products/1` and submit the same payload.
3. Show that the page renders the text as escaped HTML entities and no script executes.
4. Screenshot name: `xss-02-fixed-escaped.png`.

## 3d. Live Attack: IDOR On Order Details

### Vulnerable Proof

1. Logged in as `alice`, open `http://127.0.0.1:5001/orders/1`.
2. Show that the order is owned by a different user and the line items are visible.
3. Screenshot name: `idor-01-vulnerable-other-order.png`.

### Fix Proof

Open the fixed build at `http://127.0.0.1:5000/orders/1`. There is no such route, so the server returns a 404. The fixed app exposes orders only through `/profile/orders` filtered by `current_user.id`.

## 3e. Live Attack: Debug, User Dump, And Bulk Export

### Vulnerable Proof

1. From a fresh tab without cookies, open `http://127.0.0.1:5001/debug` and show the secrets JSON.
2. Open `http://127.0.0.1:5001/api/admin/users` and show the users with `weak_password_hash` and bcrypt hashes.
3. Open `http://127.0.0.1:5001/api/export` and show that every table contents is dumped.
4. Screenshots: `debug-01-vulnerable-secrets.png`, `userdump-01-vulnerable-md5.png`, `export-01-vulnerable-bulk-dump.png`.

### Fix Proof

Open the same paths on `http://127.0.0.1:5000/`. The server responds with 404. Mention that `/healthz` is the only diagnostic endpoint and that no debug or export endpoints exist in production.

## 3f. Live Attack: Weak Password Registration

### Vulnerable Proof

1. Open `http://127.0.0.1:5001/auth/register`.
2. Register `weakuser_demo` with password `a`.
3. Log in as `weakuser_demo / a` and show that the dashboard loads.
4. Screenshot name: `weakpwd-01-vulnerable-accepted.png`.

### Fix Proof

1. Open `http://127.0.0.1:5000/auth/register`.
2. Try to register `fixed_weak_user` with password `a`.
3. Show the validation error and confirm the user cannot log in.
4. Screenshot name: `weakpwd-02-fixed-rejected.png`.

## 4. Optional Attack 3: Open Redirect

### Vulnerable Proof

1. Open `http://127.0.0.1:5001/auth/login?next=https://example.com/phishing`.
2. Log in as `bob` / `Bob1234!`.
3. Show the browser redirects to the external site.
4. Screenshot name: `redirect-01-vulnerable-external.png`.

### Fix Proof

1. Open `http://127.0.0.1:5000/auth/login?next=https://example.com/phishing`.
2. Log in as `bob` / `Bob1234!`.
3. Show the browser stays on the local product page.
4. Screenshot name: `redirect-02-fixed-local.png`.

## 5. Pipeline Live Demo

Do not wait for full DAST during the presentation if time is short.

1. Open GitHub Actions.
2. Select `DevSecOps Pipeline`.
3. Click `Run workflow`.
4. Show the jobs starting:
   - SAST, SCA, and Regression Tests
   - Dockerized DAST
5. Then open the most recent completed run and show:
   - pytest passed
   - Bandit passed
   - pip-audit passed
   - ZAP report artifact exists

Presentation line:

> We are triggering the same pipeline live. Since DAST can take several minutes, this previous completed run shows the full SAST, SCA, DAST artifacts and quality gates.

## 6. Final Screenshot Checklist

Save all screenshots under `Exploitation/Proofs/` using these exact names so the per-vulnerability report renders correctly:

- `rbac-01-vulnerable-alice-admin.png`
- `rbac-02-fixed-alice-denied.png`
- `rbac-03-fixed-admin-allowed.png`
- `csrf-01-vulnerable-profile-changed.png`
- `csrf-02-fixed-forbidden.png`
- `redirect-01-vulnerable-external.png`
- `redirect-02-fixed-local.png`
- `sqli-01-vulnerable-email-leak.png`
- `sqli-02-fixed-no-leak.png`
- `xss-01-vulnerable-script-tag.png`
- `xss-02-fixed-escaped.png`
- `idor-01-vulnerable-other-order.png`
- `debug-01-vulnerable-secrets.png`
- `userdump-01-vulnerable-md5.png`
- `export-01-vulnerable-bulk-dump.png`
- `weakpwd-01-vulnerable-accepted.png`
- `weakpwd-02-fixed-rejected.png`

Pipeline screenshots (place under `reports/evidence/` alongside the existing folder README):

- `pipeline-01-triggered-live.png`
- `pipeline-02-completed-run.png`
- `pipeline-03-artifacts.png`
