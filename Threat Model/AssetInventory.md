# 2. Asset Inventory

| Asset | Description | Location | Security Objective |
|-------|-------------|----------|--------------------|
| User Credentials | Customer and admin login passwords protected by bcrypt | SQLite `users.password_hash` | Confidentiality |
| Session Tokens | Flask-Login signed session cookies issued after login | Browser cookie, Flask session store | Confidentiality, Integrity |
| Flask SECRET_KEY | Secret used to sign sessions, CSRF tokens, and flash messages | `.env`, Docker environment variables | Confidentiality |
| RBAC Role Flag | `users.role` value that decides admin access | SQLite `users.role` | Integrity |
| Product Catalog | Items shown to customers and managed by admin CRUD | SQLite `products` | Integrity, Availability |
| Customer Orders | Order headers and line items for paid checkouts | SQLite `orders`, `order_items` | Integrity, Confidentiality |
| Product Reviews | User-submitted text and ratings displayed publicly | SQLite `reviews` | Integrity |
| Uploaded Avatars | User-controlled image files stored on disk | `static/uploads/`, Docker volume `app-uploads` | Integrity, Availability |
| TLS Private Key | Self-signed certificate used by Nginx during demo | `certs/privkey.pem` | Confidentiality, Integrity |
| Pipeline Artifacts | Bandit, pip-audit, and ZAP reports stored by Actions | GitHub Actions artifacts | Confidentiality, Integrity |
