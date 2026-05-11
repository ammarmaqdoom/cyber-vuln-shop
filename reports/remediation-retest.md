# Remediation and Re-Test Report

## Remediation Summary

| ID | Root Cause | Remediation | Re-Test Method | Status |
| --- | --- | --- | --- | --- |
| EXP-01 | Admin decorator did not evaluate role correctly | `User.is_admin` property and strict admin decorator check | Pytest non-admin/admin access tests | Fixed |
| EXP-02 | POST forms lacked CSRF tokens | Flask-WTF `CSRFProtect` and hidden tokens on forms | Manual form submission and ZAP scan | Fixed |
| EXP-03 | Login accepted untrusted `next` URL | Same-host redirect validation | Manual login redirect test | Fixed |
| EXP-04 | Missing cart models and wrong order item field | Added `Cart`/`CartItem`; fixed checkout total and `unit_price` | Pytest checkout regression | Fixed |
| EXP-05 | No CI security gates | Added GitHub Actions SAST/SCA/DAST workflow | GitHub Actions run and artifacts | Fixed |

## Regression Tests Added

The test suite in `tests/test_security_baseline.py` verifies:

- Non-admin users are redirected away from `/admin`.
- Admin users can access the admin dashboard.
- Product search returns expected products.
- Cart checkout creates persisted orders with correct totals and unit prices.

## Re-Test Checklist Before Submission

1. Run `pytest -q` locally and capture output.
2. Run GitHub Actions `DevSecOps Pipeline`.
3. Download `sast-sca-reports` and `dast-reports` artifacts.
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
