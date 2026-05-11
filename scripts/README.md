# scripts/

Utility scripts for the Cyber Vuln Shop DevSecOps project.

---

## capture_screenshots.py

Playwright-based proof-of-concept capture script.  
It seeds the database, starts both Flask apps (if not already running), then
walks through every documented vulnerability and saves a PNG screenshot to
`Exploitation/Proofs/`.

### Prerequisites

```
pip install playwright
python -m playwright install chromium
```

### Run

```
py -3 scripts/capture_screenshots.py
```

Run from any directory — the script resolves all paths relative to itself.
Both apps must be startable with `py -3 app.py` (port 5000) and
`py -3 demo/vulnerable_app.py` (port 5001); the script will start them
automatically if they are not already listening.

### Output

17 PNG files are written to `Exploitation/Proofs/`:

| Filename | Vulnerability |
|---|---|
| rbac-01-vulnerable-alice-admin.png | Broken RBAC — alice sees admin on 5001 |
| rbac-02-fixed-alice-denied.png | RBAC fixed — alice redirected on 5000 |
| rbac-03-fixed-admin-allowed.png | RBAC fixed — admin allowed on 5000 |
| csrf-01-vulnerable-profile-changed.png | CSRF — profile silently updated on 5001 |
| csrf-02-fixed-forbidden.png | CSRF fixed — 400 response on 5000 |
| redirect-01-vulnerable-external.png | Open redirect to example.com on 5001 |
| redirect-02-fixed-local.png | Redirect fixed — stays on /products/ on 5000 |
| sqli-01-vulnerable-email-leak.png | SQL injection leaks user emails on 5001 |
| sqli-02-fixed-no-leak.png | SQLi fixed — empty result on 5000 |
| xss-01-vulnerable-script-tag.png | Stored XSS raw script tag on 5001 |
| xss-02-fixed-escaped.png | XSS fixed — HTML entities on 5000 |
| idor-01-vulnerable-other-order.png | IDOR — any order accessible on 5001 |
| debug-01-vulnerable-secrets.png | /debug leaks secrets on 5001 |
| userdump-01-vulnerable-md5.png | /api/admin/users leaks MD5 hashes on 5001 |
| export-01-vulnerable-bulk-dump.png | /api/export dumps entire DB on 5001 |
| weakpwd-01-vulnerable-accepted.png | Weak password "a" accepted on 5001 |
| weakpwd-02-fixed-rejected.png | Weak password rejected on 5000 |

---

## demo_smoke_test.py

Automated smoke tests that verify each vulnerability is reproducible on the
vulnerable build and that the fix is effective on the production build.

```
py -3 scripts/demo_smoke_test.py
```

---

## check_zap_high.py

CI helper that fails the build if the ZAP DAST scan report contains any
High-severity findings.
