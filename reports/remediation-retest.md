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

The baseline test suite in `tests/test_security_baseline.py` verifies:

- Non-admin users are redirected away from `/admin`.
- Admin users can access the admin dashboard.
- Product search returns expected products.
- Cart checkout creates persisted orders with correct totals and unit prices.

The per-vulnerability validation workflow added these focused regression tests:

| ID | Issue | PR | Regression Test | Re-Test Result |
| --- | --- | --- | --- | --- |
| VULN-01 | [#1](https://github.com/ammarmaqdoom/cyber-vuln-shop/issues/1) | [#11](https://github.com/ammarmaqdoom/cyber-vuln-shop/pull/11) | `tests/test_vuln_01_rbac.py` | Passed |
| VULN-02 | [#2](https://github.com/ammarmaqdoom/cyber-vuln-shop/issues/2) | [#12](https://github.com/ammarmaqdoom/cyber-vuln-shop/pull/12) | `tests/test_vuln_02_csrf.py` | Passed |
| VULN-03 | [#3](https://github.com/ammarmaqdoom/cyber-vuln-shop/issues/3) | [#13](https://github.com/ammarmaqdoom/cyber-vuln-shop/pull/13) | `tests/test_vuln_03_open_redirect.py` | Passed |
| VULN-04 | [#4](https://github.com/ammarmaqdoom/cyber-vuln-shop/issues/4) | [#14](https://github.com/ammarmaqdoom/cyber-vuln-shop/pull/14) | `tests/test_vuln_04_sqli.py` | Passed |
| VULN-05 | [#5](https://github.com/ammarmaqdoom/cyber-vuln-shop/issues/5) | [#15](https://github.com/ammarmaqdoom/cyber-vuln-shop/pull/15) | `tests/test_vuln_05_xss.py` | Passed |
| VULN-06 | [#6](https://github.com/ammarmaqdoom/cyber-vuln-shop/issues/6) | [#16](https://github.com/ammarmaqdoom/cyber-vuln-shop/pull/16) | `tests/test_vuln_06_idor.py` | Passed |
| VULN-07 | [#7](https://github.com/ammarmaqdoom/cyber-vuln-shop/issues/7) | [#17](https://github.com/ammarmaqdoom/cyber-vuln-shop/pull/17) | `tests/test_vuln_07_debug_endpoint.py` | Passed |
| VULN-08 | [#8](https://github.com/ammarmaqdoom/cyber-vuln-shop/issues/8) | [#18](https://github.com/ammarmaqdoom/cyber-vuln-shop/pull/18) | `tests/test_vuln_08_user_dump.py` | Passed |
| VULN-09 | [#9](https://github.com/ammarmaqdoom/cyber-vuln-shop/issues/9) | [#19](https://github.com/ammarmaqdoom/cyber-vuln-shop/pull/19) | `tests/test_vuln_09_db_export.py` | Passed |
| VULN-10 | [#10](https://github.com/ammarmaqdoom/cyber-vuln-shop/issues/10) | [#20](https://github.com/ammarmaqdoom/cyber-vuln-shop/pull/20) | `tests/test_vuln_10_weak_password.py` | Passed |

Final local command: `py -3 -m pytest -q` passed with 21 tests. Fresh GitHub Actions run [`25698381062`](https://github.com/ammarmaqdoom/cyber-vuln-shop/actions/runs/25698381062) passed SAST, SCA, regression tests, and DAST.

## Re-Test Checklist Before Submission

1. Local pytest passed with 21 tests.
2. GitHub Actions `DevSecOps Pipeline` run `25698381062` passed.
3. `sast-reports`, `sca-reports`, and `dast-reports` artifacts were uploaded and downloaded locally.
4. Required vulnerability proof screenshots were captured in `Exploitation/Proofs/`.
5. Pipeline evidence screenshots were captured in `reports/evidence/`.
6. Demonstrate HTTPS at `https://<machine-ip>/` during presentation.

## Residual Risks Accepted

| Risk | Rationale | Owner |
| --- | --- | --- |
| SQLite instead of production DB | Acceptable for course demo and small local deployment. | App team |
| Self-signed certificate | Acceptable for presentation where no public domain is available. | DevOps team |
| No full audit log | Time-boxed; document as future improvement. | Security team |
