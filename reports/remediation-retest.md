# Remediation and Re-Test Report

## Remediation Summary

| ID | Root Cause | Remediation | Re-Test Method | Status |
| --- | --- | --- | --- | --- |
| VULN-01 | Admin guard only required authentication | `User.is_admin` property and strict admin decorator check | Screenshot proof + pytest non-admin/admin access tests | Fixed |
| VULN-02 | POST forms lacked CSRF tokens | Flask-WTF `CSRFProtect` and hidden tokens on forms | CSRF attack page rejected with missing-token error | Fixed |
| VULN-03 | Login accepted untrusted `next` URL | Same-host redirect validation | Vulnerable external redirect vs fixed local redirect screenshots | Fixed |
| VULN-04 | Product search concatenated raw SQL | SQLAlchemy parameterised query/filter flow | SQLi payload leaks e-mails only on vulnerable build | Fixed |
| VULN-05 | Review text rendered as trusted HTML | Jinja autoescaping, no `safe` rendering for reviews | XSS executes on vulnerable build and is escaped on fixed build | Fixed |
| VULN-06 | Order route lacked owner check | Enforced order ownership before rendering details | IDOR screenshot shows vulnerable cross-user read; fixed route denies non-owner | Fixed |
| VULN-07 | Debug endpoint exposed environment secrets | No debug endpoint in production app; debug disabled | Vulnerable debug screenshot + DAST high-risk gate pass | Fixed |
| VULN-08 | User dump exposed weak MD5 hashes | Removed unauthenticated dump endpoint and legacy weak hash exposure | Vulnerable dump screenshot + fixed app route absence | Fixed |
| VULN-09 | Database export required no authentication | Removed unauthenticated export endpoint | Vulnerable export screenshot + fixed app route absence | Fixed |
| VULN-10 | Registration accepted trivially weak passwords | Minimum 8-character password validation | Weak-password accepted/rejected screenshots | Fixed |
| PIPE-01 | No CI security gates | GitHub Actions SAST/SCA/tests/DAST workflow with quality gates | Successful workflow run `25667361027` and artifacts | Fixed |

## Regression Tests Added

The test suite in `tests/test_security_baseline.py` verifies:

- Non-admin users are redirected away from `/admin`.
- Admin users can access the admin dashboard.
- Product search returns expected products.
- Cart checkout creates persisted orders with correct totals and unit prices.

## Re-Test Checklist Before Submission

1. Run `pytest -q` locally and capture output.
2. Run GitHub Actions `DevSecOps Pipeline`.
3. Download `sast-reports`, `sca-reports`, and `dast-reports` artifacts.
4. Add screenshots of:
   - Passing pytest job.
   - Bandit artifact.
   - pip-audit artifact.
   - ZAP HTML report.
   - Admin RBAC denial for `alice`.
   - Admin access for `admin`.
5. Demonstrate HTTPS at `https://<machine-ip>/` during presentation.

## Residual Risks Accepted

| Risk | Rationale | Owner |
| --- | --- | --- |
| SQLite instead of production DB | Acceptable for course demo and small local deployment. | App team |
| Self-signed certificate | Acceptable for presentation where no public domain is available. | DevOps team |
| No full audit log | Time-boxed; document as future improvement. | Security team |
