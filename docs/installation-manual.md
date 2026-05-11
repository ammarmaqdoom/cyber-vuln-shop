# Installation and Operations Manual

## Purpose

This manual explains how to install, run, seed, test, and demonstrate Cyber Vuln Shop for the DevSecOps project submission.

## Requirements

- Python 3.12+
- Docker Desktop
- PowerShell
- OpenSSL available in PATH for self-signed certificate generation
- GitHub repository with Actions enabled

## Traditional Local Run

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py
python app.py
```

Development URL: `http://127.0.0.1:5000`

## Docker HTTPS Run

The graded demo should be shown on an IP address or hostname with HTTPS, not on localhost.

```powershell
Copy-Item .env.example .env
notepad .env
.\scripts\generate-self-signed-cert.ps1 -HostName "vulnshop.local" -IpAddress "<your-machine-ip>"
docker compose up --build
docker compose exec web python seed.py
```

Demo URL examples:

- `https://<your-machine-ip>/`
- `https://vulnshop.local/`

If using `vulnshop.local`, add a local hosts entry mapping the hostname to the demo machine IP.

## Demo Checklist

1. Log in as `admin` / `Admin1234!`.
2. Show Admin Dashboard.
3. Create a product under Admin Products.
4. Update and delete a demo product.
5. Log out.
6. Log in as `alice` / `Alice1234!`.
7. Confirm admin pages redirect away for non-admin users.
8. Search/filter products.
9. Add item to cart, update quantity, checkout.
10. Show order history and profile update.

## Security Pipeline Run

GitHub Actions runs automatically on push and pull request. Manual run:

1. Open GitHub repository.
2. Go to Actions.
3. Select `DevSecOps Pipeline`.
4. Click `Run workflow`.
5. Download `sast-sca-reports` and `dast-reports` artifacts after completion.

## Operational Notes

- `SECRET_KEY` must be changed before demo.
- SQLite data is stored in Docker volume `app-data`.
- Uploaded files are stored in Docker volume `app-uploads`.
- The Nginx container terminates TLS and proxies traffic to Flask/Gunicorn.
- Self-signed certificates are acceptable for the course demo if the browser warning is acknowledged.
