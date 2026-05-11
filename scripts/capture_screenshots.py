#!/usr/bin/env python3
"""
Playwright screenshot capture for the DevSecOps Cyber Vuln Shop project.

Captures proof-of-concept screenshots for all 10 documented vulnerabilities
(17 PNG files) and saves them to  Exploitation/Proofs/.

Prerequisites
-------------
    pip install playwright
    python -m playwright install chromium

Usage
-----
    py -3 scripts/capture_screenshots.py
    (run from any directory; the script resolves paths relative to itself)
"""

import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT  = pathlib.Path(__file__).resolve().parent.parent
PROOFS_DIR = REPO_ROOT / "Exploitation" / "Proofs"
DEMO_DIR   = REPO_ROOT / "demo"

# ── Server URLs ───────────────────────────────────────────────────────────────
FIXED = "http://127.0.0.1:5000"   # fixed / production app
VULN  = "http://127.0.0.1:5001"   # intentionally vulnerable demo

# ── Required proof filenames (in report order) ────────────────────────────────
REQUIRED = [
    "rbac-01-vulnerable-alice-admin.png",
    "rbac-02-fixed-alice-denied.png",
    "rbac-03-fixed-admin-allowed.png",
    "csrf-01-vulnerable-profile-changed.png",
    "csrf-02-fixed-forbidden.png",
    "redirect-01-vulnerable-external.png",
    "redirect-02-fixed-local.png",
    "sqli-01-vulnerable-email-leak.png",
    "sqli-02-fixed-no-leak.png",
    "xss-01-vulnerable-script-tag.png",
    "xss-02-fixed-escaped.png",
    "idor-01-vulnerable-other-order.png",
    "debug-01-vulnerable-secrets.png",
    "userdump-01-vulnerable-md5.png",
    "export-01-vulnerable-bulk-dump.png",
    "weakpwd-01-vulnerable-accepted.png",
    "weakpwd-02-fixed-rejected.png",
]

# URL-encoded SQLi UNION payload  (%' UNION SELECT id, email, …  FROM users--)
SQLI_PATH = (
    "/products/?q=%25%27%20UNION%20SELECT%20id%2C%20email%2C"
    "%20%27%27%2C%200%2C%200%2C%20%27%27%2C%20%27%27%20FROM%20users--"
)
XSS_PAYLOAD = "<script>alert('xss')</script>"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_up(base: str) -> bool:
    """Return True when the server at *base* responds to a GET /."""
    try:
        urllib.request.urlopen(base + "/", timeout=2)
        return True
    except Exception:
        return False


def ensure_server(
    base: str,
    cmd: list,
    cwd: pathlib.Path,
    timeout: int = 30,
) -> "subprocess.Popen | None":
    """
    Ensure the Flask dev server at *base* is running.

    If it is already responding, return None.
    Otherwise start *cmd* from *cwd*, poll until ready, and return the Popen.
    Raises RuntimeError if it does not start within *timeout* seconds.
    """
    if _is_up(base):
        print(f"  {base}  already running.")
        return None

    print(f"  Starting  {' '.join(str(c) for c in cmd)} …")
    proc = subprocess.Popen(
        [str(c) for c in cmd],
        cwd=str(cwd),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _is_up(base):
            print(f"  {base}  ready.")
            return proc
        time.sleep(0.5)

    proc.terminate()
    raise RuntimeError(f"Server at {base} did not start within {timeout}s")


def fresh_ctx(browser: Browser) -> BrowserContext:
    """New isolated BrowserContext, 1280 × 800, 20-second default timeout."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    ctx.set_default_timeout(20_000)
    return ctx


def login_vuln(page: Page, username: str, password: str) -> None:
    """
    Login on the *vulnerable* app (port 5001).
    The form has no CSRF token and no explicit action attribute, so it POSTs
    to whatever URL is currently in the address bar.
    """
    page.goto(f"{VULN}/auth/login")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='username']", username)
    page.fill("input[name='password']", password)
    with page.expect_navigation(wait_until="networkidle", timeout=15_000):
        page.click("button[type='submit']")


def login_fixed(page: Page, username: str, password: str) -> None:
    """
    Login on the *fixed* app (port 5000).
    The rendered form already contains a CSRF token hidden-input; Playwright
    submits it automatically when we click the submit button.
    """
    page.goto(f"{FIXED}/auth/login")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='username']", username)
    page.fill("input[name='password']", password)
    with page.expect_navigation(wait_until="networkidle", timeout=15_000):
        page.click("button[type='submit']")


def snap(page: Page, name: str, saved: list) -> None:
    """
    Wait for network-idle, take a full-page PNG, and record the path.
    Re-tries once on failure.
    """
    PROOFS_DIR.mkdir(parents=True, exist_ok=True)
    path = PROOFS_DIR / name
    for attempt in range(2):
        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
            page.screenshot(path=str(path), full_page=True)
            saved.append(str(path))
            print(f"  ✓  {name}")
            return
        except Exception as exc:
            if attempt == 0:
                print(f"  ⚠  {name}  retry after: {exc}")
                time.sleep(1)
            else:
                print(f"  ✗  {name}  FAILED: {exc}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    PROOFS_DIR.mkdir(parents=True, exist_ok=True)
    saved: list = []
    server_procs: list = []

    # ── 1 · Reseed ────────────────────────────────────────────────────────────
    print("\n[1/3] Reseeding database …")
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "seed.py")],
        cwd=str(REPO_ROOT),
        check=True,
    )
    print("  Database seeded.")

    # ── 2 · Start servers ────────────────────────────────────────────────────
    print("\n[2/3] Checking / starting servers …")
    p_fixed = ensure_server(
        FIXED,
        [sys.executable, str(REPO_ROOT / "app.py")],
        REPO_ROOT,
    )
    if p_fixed:
        server_procs.append(p_fixed)

    p_vuln = ensure_server(
        VULN,
        [sys.executable, str(REPO_ROOT / "demo" / "vulnerable_app.py")],
        REPO_ROOT,
    )
    if p_vuln:
        server_procs.append(p_vuln)

    # ── 3 · Capture screenshots ───────────────────────────────────────────────
    print("\n[3/3] Capturing screenshots …\n")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=False)

            # ── RBAC ──────────────────────────────────────────────────────────
            print("── RBAC ──")

            # rbac-01 · alice reaches admin dashboard on vulnerable build
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                login_vuln(pg, "alice", "Alice1234!")
                pg.goto(f"{VULN}/admin")
                snap(pg, "rbac-01-vulnerable-alice-admin.png", saved)

            # rbac-02 · alice is denied on fixed build (redirect to login)
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                login_fixed(pg, "alice", "Alice1234!")
                pg.goto(f"{FIXED}/admin")
                snap(pg, "rbac-02-fixed-alice-denied.png", saved)

            # rbac-03 · admin is allowed on fixed build
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                login_fixed(pg, "admin", "Admin1234!")
                pg.goto(f"{FIXED}/admin")
                snap(pg, "rbac-03-fixed-admin-allowed.png", saved)

            # ── Open Redirect ─────────────────────────────────────────────────
            print("\n── Open Redirect ──")
            BAD_NEXT = "https://example.com/phishing"

            # redirect-01 · vulnerable: login redirects to external example.com
            # The vulnerable login template has NO explicit form action, so it
            # POSTs to the current URL (which carries ?next=…).  The server then
            # reads request.args["next"] and blindly redirects there.
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                pg.goto(f"{VULN}/auth/login?next={BAD_NEXT}")
                pg.wait_for_load_state("networkidle")
                pg.fill("input[name='username']", "admin")
                pg.fill("input[name='password']", "Admin1234!")
                try:
                    with pg.expect_navigation(
                        wait_until="domcontentloaded", timeout=20_000
                    ):
                        pg.click("button[type='submit']")
                    pg.wait_for_load_state("networkidle", timeout=10_000)
                except Exception as exc:
                    # external redirect might be slow; screenshot whatever loaded
                    print(f"  ℹ  redirect-01 navigation note: {exc}")
                snap(pg, "redirect-01-vulnerable-external.png", saved)

            # redirect-02 · fixed: login ignores unsafe next, stays on /products/
            # The fixed template uses action="{{ url_for('auth.login') }}" which
            # strips the query string, so the POST carries no ?next=; the server
            # falls back to /products/.
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                pg.goto(f"{FIXED}/auth/login?next={BAD_NEXT}")
                pg.wait_for_load_state("networkidle")
                pg.fill("input[name='username']", "admin")
                pg.fill("input[name='password']", "Admin1234!")
                with pg.expect_navigation(wait_until="networkidle", timeout=15_000):
                    pg.click("button[type='submit']")
                snap(pg, "redirect-02-fixed-local.png", saved)

            # ── SQL Injection ─────────────────────────────────────────────────
            print("\n── SQL Injection ──")

            # sqli-01 · vulnerable: UNION SELECT leaks user e-mails as product names
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                login_vuln(pg, "alice", "Alice1234!")
                pg.goto(f"{VULN}{SQLI_PATH}")
                snap(pg, "sqli-01-vulnerable-email-leak.png", saved)

            # sqli-02 · fixed: parameterised query returns empty result set
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                login_fixed(pg, "alice", "Alice1234!")
                pg.goto(f"{FIXED}{SQLI_PATH}")
                snap(pg, "sqli-02-fixed-no-leak.png", saved)

            # ── Stored XSS ────────────────────────────────────────────────────
            print("\n── Stored XSS ──")

            # xss-01 · vulnerable: alice posts a <script> review; page renders it
            #          raw (|safe filter).  We inject a visible DOM marker so the
            #          stored payload is clearly visible in the screenshot.
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                # Dismiss any alert() dialogs the stored XSS may trigger
                pg.on("dialog", lambda d: d.dismiss())
                login_vuln(pg, "alice", "Alice1234!")
                pg.goto(f"{VULN}/products/1")
                pg.wait_for_load_state("networkidle")
                pg.fill("textarea[name='text']", XSS_PAYLOAD)
                with pg.expect_navigation(wait_until="networkidle", timeout=15_000):
                    pg.click("button[type='submit']")
                # Inject a bright red marker next to any stored <script> so the
                # screenshot shows the raw payload visually
                try:
                    pg.evaluate(
                        """
                        () => {
                            document.querySelectorAll('p').forEach(function (p) {
                                var s = p.querySelector('script');
                                if (s) {
                                    var m = document.createElement('pre');
                                    m.style.cssText = (
                                        'background:#fee2e2;color:#b91c1c;'
                                        'border:2px solid #dc2626;padding:8px;'
                                        'margin:4px 0;font-size:13px;white-space:pre-wrap'
                                    );
                                    m.textContent =
                                        '[XSS PAYLOAD STORED — rendered raw by |safe filter]\\n'
                                        + '<script>' + s.textContent + '<\\/script>';
                                    p.parentNode.insertBefore(m, p.nextSibling);
                                }
                            });
                        }
                        """
                    )
                except Exception:
                    pass
                snap(pg, "xss-01-vulnerable-script-tag.png", saved)

            # xss-02 · fixed: bob posts the same payload; Jinja autoescape shows
            #          HTML entities instead of executing the script.
            #          (alice's XSS review is already in the shared DB and is
            #          also visible here — escaped — which strengthens the proof.)
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                login_fixed(pg, "bob", "Bob1234!")
                pg.goto(f"{FIXED}/products/1")
                pg.wait_for_load_state("networkidle")
                # The review form uses a CSRF token that is already rendered in
                # the hidden input; fill + click submits it automatically.
                pg.fill("input[name='rating']", "5")
                pg.fill("input[name='text']", XSS_PAYLOAD)
                with pg.expect_navigation(wait_until="networkidle", timeout=15_000):
                    pg.click("button:has-text('Submit review')")
                snap(pg, "xss-02-fixed-escaped.png", saved)

            # ── IDOR ──────────────────────────────────────────────────────────
            print("\n── IDOR ──")

            # idor-01 · alice views /orders/1 on vulnerable; no ownership check
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                login_vuln(pg, "alice", "Alice1234!")
                pg.goto(f"{VULN}/orders/1")
                snap(pg, "idor-01-vulnerable-other-order.png", saved)

            # ── Weak Password ─────────────────────────────────────────────────
            print("\n── Weak Password ──")

            # weakpwd-01 · register weakuser_demo / "a" on vulnerable (no policy),
            #             then login and screenshot the products page.
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                pg.goto(f"{VULN}/auth/register")
                pg.wait_for_load_state("networkidle")
                pg.fill("input[name='username']", "weakuser_demo")
                pg.fill("input[name='email']", "weakuser_demo@example.com")
                pg.fill("input[name='password']", "a")
                # Registration success → redirect to login
                with pg.expect_navigation(wait_until="networkidle", timeout=15_000):
                    pg.click("button[type='submit']")
                # Login with the weak password
                pg.fill("input[name='username']", "weakuser_demo")
                pg.fill("input[name='password']", "a")
                with pg.expect_navigation(wait_until="networkidle", timeout=15_000):
                    pg.click("button[type='submit']")
                snap(pg, "weakpwd-01-vulnerable-accepted.png", saved)

            # ── CSRF ──────────────────────────────────────────────────────────
            # (done after xss-02 so bob's credentials are still intact)
            print("\n── CSRF ──")

            # csrf-01 · bob logs in to vulnerable; we POST /profile/update
            #           WITHOUT a CSRF token via fetch() in the same-origin page
            #           context (simulating the cross-site attack: the server
            #           accepts any POST because WTF_CSRF_ENABLED=False).
            #           We then navigate to /profile to show the changed values.
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                login_vuln(pg, "bob", "Bob1234!")
                pg.evaluate(
                    """
                    async () => {
                        await fetch('/profile/update', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded'
                            },
                            body: 'username=csrf_owned_user'
                                  + '&email=csrf-owned%40example.com'
                        });
                    }
                    """
                )
                pg.goto(f"{VULN}/profile")
                snap(pg, "csrf-01-vulnerable-profile-changed.png", saved)

            # csrf-02 · alice logs in to fixed; same no-token POST → HTTP 400
            #           (Flask-WTF CSRFProtect rejects it).  We capture the 400
            #           response body and render it for the screenshot.
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                login_fixed(pg, "alice", "Alice1234!")
                result = pg.evaluate(
                    """
                    async () => {
                        const resp = await fetch('/profile/update', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded'
                            },
                            body: 'username=csrf_hacked&email=csrf%40hack.com'
                        });
                        const text = await resp.text();
                        return { status: resp.status, text: text };
                    }
                    """
                )
                if result["status"] != 400:
                    print(
                        f"  ⚠  csrf-02: expected HTTP 400, got {result['status']}"
                    )
                pg.set_content(result["text"])
                snap(pg, "csrf-02-fixed-forbidden.png", saved)

            # ── Unauthenticated Endpoints ─────────────────────────────────────
            print("\n── Unauthenticated Endpoints ──")

            # debug-01 · /debug leaks Flask secret, JWT secret, API keys
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                pg.goto(f"{VULN}/debug")
                snap(pg, "debug-01-vulnerable-secrets.png", saved)

            # userdump-01 · /api/admin/users returns all users with MD5 hashes
            #              (weakuser_demo is now in the DB from weakpwd-01)
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                pg.goto(f"{VULN}/api/admin/users")
                snap(pg, "userdump-01-vulnerable-md5.png", saved)

            # export-01 · /api/export dumps every table in the database
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                pg.goto(f"{VULN}/api/export")
                snap(pg, "export-01-vulnerable-bulk-dump.png", saved)

            # weakpwd-02 · attempt to register with password "a" on fixed build;
            #              server rejects it with "Password must be at least 8
            #              characters." flash message.
            print("\n── Weak Password (fixed) ──")
            with fresh_ctx(browser) as ctx:
                pg = ctx.new_page()
                pg.goto(f"{FIXED}/auth/register")
                pg.wait_for_load_state("networkidle")
                pg.fill("input[name='username']", "weakuser_demo")
                pg.fill("input[name='email']", "weakuser_demo@example.com")
                pg.fill("input[name='password']", "a")
                pg.click("button[type='submit']")
                # Server returns 200 with re-rendered form + flash (no redirect)
                pg.wait_for_load_state("networkidle")
                snap(pg, "weakpwd-02-fixed-rejected.png", saved)

            browser.close()

    finally:
        for proc in server_procs:
            proc.terminate()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print(f"Captured {len(saved)} / {len(REQUIRED)} screenshots.\n")
    for p in saved:
        print(f"  {p}")

    missing = [n for n in REQUIRED if not (PROOFS_DIR / n).exists()]
    if missing:
        print(f"\n⚠  Missing ({len(missing)}):")
        for m in missing:
            print(f"  {m}  — could not be captured automatically")
    else:
        print("\n✓  All 17 screenshots captured successfully.")


if __name__ == "__main__":
    main()
