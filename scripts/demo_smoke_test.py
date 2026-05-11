"""Smoke-test the live attack chain.

Runs against the vulnerable demo on http://127.0.0.1:5001 and the
remediated fixed app on http://127.0.0.1:5000. Each finding from
``Exploitation/ExploitationReport.md`` has a matching assertion.
"""

import json
import subprocess
import sys
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, HTTPRedirectHandler, Request, build_opener


FIXED = "http://127.0.0.1:5000"
VULN = "http://127.0.0.1:5001"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


def opener(follow_redirects: bool = True):
    handlers = [HTTPCookieProcessor(CookieJar())]
    if not follow_redirects:
        handlers.append(NoRedirect())
    return build_opener(*handlers)


def csrf_token(html: str) -> str | None:
    marker = 'name="csrf_token"'
    if marker not in html:
        return None
    return html.split(marker, 1)[1].split('value="', 1)[1].split('"', 1)[0]


def get(client, url):
    return client.open(url, timeout=10)


def post(client, url, data):
    encoded = urlencode(data).encode()
    return client.open(Request(url, data=encoded, method="POST"), timeout=10)


def login(base, username, password, *, follow_redirects=True, next_url=None):
    client = opener(follow_redirects=follow_redirects)
    login_url = f"{base}/auth/login"
    if next_url:
        login_url = f"{login_url}?next={next_url}"
    page = get(client, login_url).read().decode()
    data = {"username": username, "password": password}
    token = csrf_token(page)
    if token:
        data["csrf_token"] = token
    try:
        response = client.open(
            Request(login_url, data=urlencode(data).encode(), method="POST"), timeout=10
        )
    except HTTPError as exc:
        response = exc
    return client, response


def body(response) -> str:
    return response.read().decode(errors="replace")


def assert_true(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"{status}: {label}")
    if not condition:
        raise SystemExit(1)


def reseed():
    subprocess.run([sys.executable, "seed.py"], check=True)


def main() -> None:
    reseed()
    # 1. Broken RBAC (vulnerable)
    vuln_alice, _ = login(VULN, "alice", "Alice1234!")
    assert_true(
        "V1 Vulnerable: alice can read admin dashboard",
        "Admin Dashboard - Vulnerable" in body(get(vuln_alice, f"{VULN}/admin")),
    )

    # 1. Broken RBAC (fixed)
    fixed_alice, _ = login(FIXED, "alice", "Alice1234!")
    fixed_alice_admin = get(fixed_alice, f"{FIXED}/admin")
    assert_true(
        "V1 Fixed: alice redirected away from /admin",
        fixed_alice_admin.geturl() != f"{FIXED}/admin",
    )
    fixed_admin, _ = login(FIXED, "admin", "Admin1234!")
    assert_true(
        "V1 Fixed: admin sees Admin Dashboard",
        "Admin Dashboard" in body(get(fixed_admin, f"{FIXED}/admin")),
    )

    # 2. CSRF profile takeover
    vuln_bob, _ = login(VULN, "bob", "Bob1234!")
    post(
        vuln_bob,
        f"{VULN}/profile/update",
        {"username": "csrf_owned_user", "email": "csrf-owned@example.com"},
    )
    assert_true(
        "V2 Vulnerable: profile changed without CSRF token",
        "csrf_owned_user" in body(get(vuln_bob, f"{VULN}/profile")),
    )

    fixed_csrf_user, _ = login(FIXED, "alice", "Alice1234!")
    try:
        post(
            fixed_csrf_user,
            f"{FIXED}/profile/update",
            {"username": "csrf_should_fail", "email": "csrf-fail@example.com"},
        )
        fixed_csrf_blocked = False
    except HTTPError as exc:
        fixed_csrf_blocked = exc.code == 400
    assert_true(
        "V2 Fixed: profile update without CSRF token rejected with 400",
        fixed_csrf_blocked,
    )

    # 3. Open redirect
    _, vuln_redirect = login(
        VULN, "admin", "Admin1234!", follow_redirects=False, next_url="https://example.com/phishing"
    )
    assert_true(
        "V3 Vulnerable: login redirects to external host",
        vuln_redirect.headers.get("Location") == "https://example.com/phishing",
    )
    _, fixed_redirect = login(
        FIXED, "admin", "Admin1234!", follow_redirects=False, next_url="https://example.com/phishing"
    )
    assert_true(
        "V3 Fixed: external next URL ignored",
        fixed_redirect.headers.get("Location") != "https://example.com/phishing",
    )

    # 4. SQL injection in product search
    sqli_payload = "%' UNION SELECT id, email, '', 0, 0, '', '' FROM users--"
    sqli_html = body(get(vuln_alice, f"{VULN}/products/?q={urlencode({'': sqli_payload})[1:]}"))
    assert_true(
        "V4 Vulnerable: SQLi returns user data in product search",
        "alice@example.com" in sqli_html or "admin@vulnshop.local" in sqli_html,
    )
    fixed_sqli_html = body(get(fixed_alice, f"{FIXED}/products/?q={urlencode({'': sqli_payload})[1:]}"))
    assert_true(
        "V4 Fixed: SQLi payload does not leak user emails",
        "alice@example.com" not in fixed_sqli_html
        and "admin@vulnshop.local" not in fixed_sqli_html,
    )

    # Re-seed before the remaining tests because vulnerable CSRF mutated bob's
    # profile in the shared SQLite database.
    reseed()

    # 5. Stored XSS in product reviews
    vuln_alice, _ = login(VULN, "alice", "Alice1234!")
    post(
        vuln_alice,
        f"{VULN}/products/1",
        {"rating": "5", "text": "<script>alert('xss')</script>"},
    )
    xss_html = body(get(vuln_alice, f"{VULN}/products/1"))
    assert_true(
        "V5 Vulnerable: script tag rendered without escaping",
        "<script>alert('xss')</script>" in xss_html,
    )
    fixed_review_user, _ = login(FIXED, "bob", "Bob1234!")
    page = body(get(fixed_review_user, f"{FIXED}/products/1"))
    token = csrf_token(page)
    post(
        fixed_review_user,
        f"{FIXED}/products/1/reviews",
        {
            "csrf_token": token,
            "rating": "5",
            "text": "<script>alert('xss')</script>",
        },
    )
    fixed_xss = body(get(fixed_review_user, f"{FIXED}/products/1"))
    assert_true(
        "V5 Fixed: review HTML escaped",
        "<script>alert('xss')</script>" not in fixed_xss
        and "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;" in fixed_xss,
    )

    # 6. IDOR — alice reads admin user's order #1
    idor_html = body(get(vuln_alice, f"{VULN}/orders/1"))
    assert_true(
        "V6 Vulnerable: alice reads someone else's order by ID",
        "Order #1" in idor_html,
    )
    # Fixed app does not expose a /orders/<id> route; cart/order pages are scoped to current user.

    # 7. Unauthenticated user dump exposing weak hashes
    public = opener()
    user_dump = json.loads(body(get(public, f"{VULN}/api/admin/users")))
    assert_true(
        "V7 Vulnerable: unauthenticated /api/admin/users returns users",
        any(user.get("weak_password_hash") for user in user_dump),
    )

    # 8. Debug endpoint leaks secrets
    debug = json.loads(body(get(public, f"{VULN}/debug")))
    assert_true(
        "V8 Vulnerable: /debug endpoint exposes secrets",
        "LLM_API_KEY" in debug and "JWT_SECRET" in debug,
    )

    # 9. Unauthenticated bulk export
    export = json.loads(body(get(public, f"{VULN}/api/export")))
    assert_true(
        "V9 Vulnerable: /api/export dumps users table",
        any(row.get("email") for row in export.get("users", [])),
    )

    # 10. Weak password registration accepted
    weak = opener()
    weak_username = "weakuser_demo"
    page = body(get(weak, f"{VULN}/auth/register"))
    post(
        weak,
        f"{VULN}/auth/register",
        {"username": weak_username, "email": f"{weak_username}@example.com", "password": "a"},
    )
    weak_login, _ = login(VULN, weak_username, "a")
    assert_true(
        "V10 Vulnerable: account with one-character password can log in",
        "Vulnerable Demo Products" in body(get(weak_login, f"{VULN}/products/")),
    )
    # Fixed app blocks weak password at registration.
    fixed_weak = opener()
    page = body(get(fixed_weak, f"{FIXED}/auth/register"))
    token = csrf_token(page)
    post(
        fixed_weak,
        f"{FIXED}/auth/register",
        {
            "csrf_token": token,
            "username": "fixed_weak_user",
            "email": "fixed_weak_user@example.com",
            "password": "a",
        },
    )
    fixed_attempt, response = login(FIXED, "fixed_weak_user", "a")
    assert_true(
        "V10 Fixed: weak password rejected and login fails",
        response.geturl().endswith("/auth/login"),
    )

    print("\nAll demo attack assertions passed against vulnerable=5001 and fixed=5000.")


if __name__ == "__main__":
    main()
