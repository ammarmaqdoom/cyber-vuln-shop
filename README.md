# Cyber Vuln Shop

Cyber Vuln Shop is a small Flask e-commerce application built for a DevSecOps course submission. It demonstrates authentication, role-based access control, product CRUD, cart/checkout, database persistence, Docker deployment, and automated SAST/SCA/DAST checks.

## Table of Contents

1. [Application Features](#application-features)
2. [Default Demo Accounts](#default-demo-accounts)
3. [Local Setup](#local-setup)
4. [Docker and HTTPS Demo](#docker-and-https-demo)
5. [DevSecOps Pipeline](#devsecops-pipeline)
6. [Live Attack Demo](#live-attack-demo)
7. [Project Documents](#project-documents)
8. [GitHub Issue and Push Guideline](#github-issue-and-push-guideline)
9. [Team Contribution Areas](#team-contribution-areas)

## Application Features

- User registration, login, logout, failed-login lockout, and server-side sessions through Flask-Login.
- RBAC with `admin` and `user` roles. Admin pages are blocked for non-admin users.
- Product catalog with search and category filtering.
- Admin product CRUD: create, read, update, and delete products.
- Cart operations, checkout, order history, profile update, and validated image upload.
- SQLite database persistence through SQLAlchemy.
- CSRF protection on state-changing forms.

## Default Demo Accounts

Run `python seed.py` before the demo to create these accounts:

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin` | `Admin1234!` |
| User | `alice` | `Alice1234!` |
| User | `bob` | `Bob1234!` |

## Local Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py
python app.py
```

Open `http://127.0.0.1:5000` for local development. For final presentation, use the Docker HTTPS flow below on an IP address or hostname.

## Docker and HTTPS Demo

1. Copy `.env.example` to `.env` and replace `SECRET_KEY`.
2. Generate a self-signed certificate for the demo hostname or IP:

```powershell
.\scripts\generate-self-signed-cert.ps1 -HostName "vulnshop.local" -IpAddress "<your-machine-ip>"
```

3. Start the app behind Nginx TLS:

```powershell
docker compose up --build
```

4. Seed demo data:

```powershell
docker compose exec web python seed.py
```

5. Present the app at `https://<your-machine-ip>/` or `https://vulnshop.local/`.

## DevSecOps Pipeline

The GitHub Actions workflow in `.github/workflows/devsecops.yml` runs:

- SAST: Bandit high-severity scan.
- SCA: pip-audit dependency audit.
- Tests: pytest regression tests for RBAC and checkout.
- DAST: OWASP ZAP baseline against the Dockerized app.
- Artifacts: JSON/HTML security reports uploaded from each pipeline run.

## Live Attack Demo

For presentation, run the fixed app and vulnerable demo side by side:

```powershell
py -3 seed.py
py -3 app.py
```

```powershell
py -3 demo/vulnerable_app.py
```

- Fixed app: `http://127.0.0.1:5000`
- Vulnerable demo: `http://127.0.0.1:5001`
- Full presenter script: `reports/live-demo-runbook.md`

Live attacks included:

- Broken RBAC: non-admin `alice` accesses vulnerable `/admin`, then is blocked in the fixed app.
- CSRF: forged profile update succeeds in the vulnerable app, then fails in the fixed app.
- Open redirect: vulnerable login redirects externally, then fixed login stays local.

## Project Documents

- Installation and operations manual: `docs/installation-manual.md`
- Final report: `reports/final-report.md`
- Threat model (course rubric layout): `Threat Model/ThreatModel.md` and `Threat Model/AssetInventory.md`
- Exploitation report (course rubric layout): `Exploitation/ExploitationReport.md`
- Exploitation proof screenshots: `Exploitation/Proofs/`
- Remediation and re-test report: `reports/remediation-retest.md`
- Executive summary: `reports/executive-summary.md`
- Live demo runbook: `reports/live-demo-runbook.md`

## GitHub Issue and Push Guideline

Create a GitHub Issue before each task, then link commits using the required course format:

```text
fix #12: sanitise SQL input in login form
```

Use `feature/*` branches for new work and `fix/*` branches for remediation work. Merge through pull requests where time allows.

## Team Contribution Areas

- **Ikramah Elahi** ([@ikramahelahi](https://github.com/ikramahelahi)) — Flask application: authentication and session, RBAC enforcement, product/cart/order/profile CRUD, SQLAlchemy models, input validation, and Jinja templates.
- **Ammar Maqdoom** ([@ammarmaqdoom](https://github.com/ammarmaqdoom)) — DevSecOps platform: Docker and `docker-compose`, Nginx HTTPS reverse proxy, self-signed certificate workflow, and the GitHub Actions pipeline integrating Bandit + Semgrep (SAST), pip-audit (SCA), OWASP ZAP (DAST), pytest regression gate, and the ZAP high-finding quality gate.
- **Muhammad Mustafa** ([@huMustafa](https://github.com/huMustafa)) — Security analysis: asset inventory, STRIDE threat model (including `Threat Model/ThreatModel.tm7`), exploitation report with per-vulnerability PoCs and screenshots, executive summary, remediation/re-test report, and the final consolidated report.
