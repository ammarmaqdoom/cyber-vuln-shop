"""Generate Threat Model/ThreatModel.tm7 for the Cyber Vuln Shop project.

We take friend's `friend_threatmodel.tm7` as a structural skeleton (KnowledgeBase
and Profile sections are Microsoft TMT built-in templates, not project-specific
intellectual property), and rewrite the project-specific portions:

    * MetaInformation: project name, owner, contributors, system description.
    * DrawingSurfaceList: clear (we ship the DFD as ThreatModel.md + PNG).
    * ThreatInstances: replace 127 WhatsApp threats with our 15 STRIDE threats.
    * Notes: short pointer back to the canonical ThreatModel.md.
"""

from __future__ import annotations

import copy
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = REPO_ROOT / "Threat Model" / "ThreatModel.tm7"
# On a fresh checkout the script regenerates the file by re-reading itself.
# The skeleton is whichever of these exists first.
SKELETON_CANDIDATES = [
    OUTPUT,
    REPO_ROOT / "friend_threatmodel.tm7",
]
SKELETON = next((p for p in SKELETON_CANDIDATES if p.exists()), None)

NS_MODEL = "http://schemas.datacontract.org/2004/07/ThreatModeling.Model"
NS_ABS = "http://schemas.datacontract.org/2004/07/ThreatModeling.Model.Abstracts"
NS_SER = "http://schemas.microsoft.com/2003/10/Serialization/Arrays"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"

ET.register_namespace("", NS_MODEL)
ET.register_namespace("i", NS_XSI)

PROJECT_NAME = "Cyber Vuln Shop"
OWNER = "Ammar Maqdoom, Ikramah Elahi, Muhammad Mustafa"
CONTRIBUTORS = OWNER
REVIEWER = "Habib University - Cyber Security Course"
HIGH_LEVEL = (
    "Cyber Vuln Shop is a Flask-based e-commerce demo with public catalog, "
    "authenticated customer flows (cart, checkout, profile, orders), and an "
    "admin area for user/product/order management. It is deployed in Docker "
    "behind an Nginx TLS proxy and protected by Flask-Login session auth, "
    "Flask-WTF CSRF protection, bcrypt password hashing, and a parameterised "
    "SQLAlchemy ORM. A separately-deployed vulnerable replica intentionally "
    "exposes ten OWASP Top 10 flaws so the same DFD can be analysed in both "
    "the vulnerable and hardened states."
)
ASSUMPTIONS = (
    "1. The application is deployed in a single Docker host with the SQLite "
    "file mounted as a named volume; this is acceptable for a coursework "
    "demo but not for production scale.\n"
    "2. TLS certificates are self-signed and accepted manually by the grader's "
    "browser; the private key never leaves the demo host.\n"
    "3. GitHub Actions runners are trusted; secrets used for the pipeline live "
    "in GitHub repository secrets, not in code.\n"
    "4. There is no external SMTP, payment, or identity provider in scope; "
    "all authentication is local username/password."
)
EXTERNAL_DEPENDENCIES = (
    "Python 3.12, Flask 3.x, Flask-Login, Flask-WTF, Flask-SQLAlchemy, bcrypt, "
    "gunicorn 21.x, Nginx 1.27, SQLite 3.x, Docker Engine 24+, GitHub Actions "
    "(ubuntu-latest), Bandit, Semgrep, pip-audit, OWASP ZAP baseline."
)

# Threats from Threat Model/ThreatModel.md, section 3.2
# (id, stride_category, target, title, short_description, description,
#  priority, state)
THREATS: list[tuple[str, str, str, str, str, str, str]] = [
    (
        "T1",
        "Spoofing",
        "routes/auth.py register",
        "Weak password policy enables account takeover",
        "Registration accepts any password length, allowing trivial brute force or "
        "credential stuffing.",
        "An attacker registers (or guesses) an account with a one-character "
        "password and reuses the credential against other sites. Without a "
        "minimum-length policy, the auth boundary collapses in seconds. "
        "Mitigation: enforce >=8 character passwords (implemented) and add login "
        "lockout / rate limiting.",
        "High",
    ),
    (
        "T2",
        "Information Disclosure",
        "demo/vulnerable_app.py /api/admin/users and users.avatar",
        "Unauthenticated dump of user records including MD5 hashes",
        "Vulnerable replica exposes /users.json with MD5 password hashes that "
        "can be cracked offline.",
        "An attacker calls /users.json unauthenticated and receives every "
        "account's bcrypt hash, MD5 hash, e-mail and role. MD5 is rainbow-table "
        "ready, so even weak passwords (T1) crack in seconds. Mitigation: "
        "remove the endpoint, never store legacy hashes, require admin role.",
        "Critical",
    ),
    (
        "T3",
        "Elevation of Privilege",
        "routes/admin.py admin_required",
        "RBAC bypass on /admin endpoints",
        "Authenticated non-admin users reach admin pages because the guard only "
        "checks login state.",
        "A regular customer browses to /admin and manages users, products, or "
        "orders because the vulnerable build only verifies is_authenticated, "
        "not role. Mitigation: enforce current_user.is_admin in the "
        "admin_required decorator (implemented).",
        "High",
    ),
    (
        "T4",
        "Tampering",
        "routes/profile.py update_profile",
        "CSRF on profile and cart state changes",
        "Forms accept POSTs without a CSRF token, enabling cross-site forced "
        "actions.",
        "A logged-in user visits an attacker page that auto-submits a form to "
        "/profile/update; the browser sends the session cookie and the account "
        "is taken over. Mitigation: Flask-WTF CSRFProtect + csrf_token() on all "
        "state-changing forms (implemented).",
        "High",
    ),
    (
        "T5",
        "Spoofing",
        "routes/auth.py login next= parameter",
        "Open redirect on login next parameter",
        "Login redirects to attacker-controlled URLs supplied via ?next=.",
        "Attacker emails a phishing link of the form /auth/login?next=https://"
        "evil.tld; after credentials, the victim lands on the attacker site "
        "inside the trusted brand context. Mitigation: validate next is a "
        "relative URL on the same host (implemented).",
        "Medium",
    ),
    (
        "T6",
        "Tampering",
        "demo/vulnerable_app.py /products/ search",
        "SQL injection in product search",
        "User input concatenated into raw SQL; UNION SELECT exfiltrates user "
        "table.",
        "Payload %' UNION SELECT id, email, '', 0, 0, '', '' FROM users-- causes "
        "the vulnerable search endpoint to display every user e-mail as a "
        "product. Mitigation: parameterised ORM queries (SQLAlchemy filter) "
        "and input validation (implemented in fixed build).",
        "Critical",
    ),
    (
        "T7",
        "Tampering",
        "demo/vulnerable_app.py /products/<id>",
        "Stored XSS in product reviews",
        "Review text rendered with |safe; <script> persists and runs in every "
        "viewer.",
        "An attacker submits <script>document.title='XSS_FIRED'</script> as a "
        "review; the page title changes proving execution. Mitigation: rely on "
        "Jinja2 default autoescaping, remove |safe (implemented in fixed "
        "build).",
        "High",
    ),
    (
        "T8",
        "Information Disclosure",
        "demo/vulnerable_app.py /orders/<id>",
        "IDOR on order details",
        "Any authenticated user can read any order by changing the URL ID.",
        "Bob (id 3) browses /orders/1 and reads Alice's order with banner "
        "'Customer ID: 2 (current user ID: 3)'. Mitigation: enforce "
        "Order.user_id == current_user.id in the route (implemented).",
        "High",
    ),
    (
        "T9",
        "Information Disclosure",
        "demo/vulnerable_app.py /debug",
        "Debug endpoint leaks secrets",
        "Unauthenticated /debug returns environment variables including secret "
        "keys.",
        "/debug exposes EXPOSED_ADMIN_API_KEY, JWT_SECRET, LLM_API_KEY, "
        "SECRET_KEY. With the JWT secret, an attacker forges admin tokens. "
        "Mitigation: remove debug endpoint, store secrets in env vars only.",
        "Critical",
    ),
    (
        "T10",
        "Information Disclosure",
        "demo/vulnerable_app.py /api/export",
        "Unauthenticated bulk database export",
        "/api/export returns the full SQLite contents without authentication.",
        "Any internet client receives users, orders, products, reviews, and "
        "cart contents in a single response. Mitigation: remove endpoint; "
        "any export must require admin role and be audit-logged.",
        "Critical",
    ),
    (
        "T11",
        "Information Disclosure",
        "demo/vulnerable_app.py handle_exception",
        "Verbose error pages expose stack traces",
        "Unhandled exceptions render full Werkzeug debugger output.",
        "Stack traces reveal internal paths, frameworks, and SQL fragments that "
        "help an attacker chain other findings. Mitigation: production error "
        "handler returns a generic page; debug=False in Flask.",
        "Medium",
    ),
    (
        "T12",
        "Denial of Service",
        "demo/vulnerable_app.py login",
        "No login lockout / rate limit",
        "Login form accepts unlimited password guesses.",
        "Combined with T1 (weak passwords) this becomes a viable credential "
        "stuffing target. Mitigation: temporary lockout after N failed "
        "attempts (implemented for the fixed build).",
        "Medium",
    ),
    (
        "T13",
        "Tampering",
        ".github/workflows/devsecops.yml",
        "Pipeline ships without quality gates",
        "If SAST/SCA/DAST jobs do not fail on high findings, vulnerable code "
        "reaches main unnoticed.",
        "A team member could disable the failure conditions on the security "
        "scans and merge to main. Mitigation: scripts/check_zap_high.py + "
        "Bandit severity gate fail the job on high findings.",
        "Medium",
    ),
    (
        "T14",
        "Information Disclosure",
        "certs/privkey.pem",
        "TLS private key committed to git",
        "A developer commits certs/privkey.pem and the demo HTTPS identity is "
        "leaked.",
        "If the self-signed key is added to version control, anybody who clones "
        "the repository can impersonate the demo server. Mitigation: certs/ is "
        ".gitignored, only certs/.gitkeep is tracked.",
        "Medium",
    ),
    (
        "T15",
        "Repudiation",
        "routes/admin.py",
        "Admin actions have no audit trail",
        "Destructive product or user changes are not logged.",
        "A malicious or coerced admin can change prices or roles and the team "
        "cannot prove who did it after the fact. Mitigation (residual risk): "
        "add an audit_log table on a follow-up sprint; currently accepted.",
        "Low",
    ),
]


def text_el(parent: ET.Element, tag: str, text: str | None = None) -> ET.Element:
    el = ET.SubElement(parent, f"{{{NS_MODEL}}}{tag}")
    if text is not None:
        el.text = text
    return el


def build_threat_instance(threat: tuple[str, str, str, str, str, str, str]) -> ET.Element:
    tid, category, target, title, short_desc, description, priority = threat
    kv_id = f"S{uuid.uuid4().hex}-{uuid.uuid4().hex[:12]}"

    kv = ET.Element(f"{{{NS_SER}}}KeyValueOfstringThreatpc_P0_PhOB")
    ET.SubElement(kv, f"{{{NS_SER}}}Key").text = kv_id

    value = ET.SubElement(kv, f"{{{NS_SER}}}Value")

    text_el(value, "ChangedBy")
    text_el(value, "DrawingSurfaceGuid", "86ef6a47-58c8-471d-99aa-532ffc1cccb6")
    text_el(value, "FlowGuid", str(uuid.uuid4()))
    text_el(value, "Id", tid)
    text_el(value, "InteractionString")
    text_el(value, "ModifiedAt", "0001-01-01T00:00:00")
    text_el(value, "Priority", priority)

    props = ET.SubElement(value, f"{{{NS_MODEL}}}Properties")

    def add_prop(key: str, val: str) -> None:
        kv2 = ET.SubElement(props, f"{{{NS_SER}}}KeyValueOfstringstring")
        ET.SubElement(kv2, f"{{{NS_SER}}}Key").text = key
        ET.SubElement(kv2, f"{{{NS_SER}}}Value").text = val

    add_prop("Title", f"{tid}: {title}")
    add_prop("UserThreatCategory", category)
    add_prop("UserThreatShortDescription", short_desc)
    add_prop("UserThreatDescription", description)
    add_prop("InteractionString", target)
    add_prop("Priority", priority)
    add_prop("State", "ManuallyAdded")

    text_el(value, "SourceGuid", "00000000-0000-0000-0000-000000000000")
    text_el(value, "State", "ManuallyAdded")
    text_el(value, "StateInformation")
    text_el(value, "TargetGuid", "00000000-0000-0000-0000-000000000000")
    text_el(value, "Title", f"{tid}: {title}")
    text_el(value, "TypeId", category[:2].upper())
    text_el(value, "Upgraded", "false")
    text_el(value, "UserThreatCategory", category)
    text_el(value, "UserThreatDescription", description)
    text_el(value, "UserThreatShortDescription", short_desc)
    text_el(value, "Wide", "false")

    return kv


def build_meta(parent: ET.Element) -> None:
    parent.clear()
    parent.tag = f"{{{NS_MODEL}}}MetaInformation"
    ET.SubElement(parent, f"{{{NS_MODEL}}}Assumptions").text = ASSUMPTIONS
    ET.SubElement(parent, f"{{{NS_MODEL}}}Contributors").text = CONTRIBUTORS
    ET.SubElement(parent, f"{{{NS_MODEL}}}ExternalDependencies").text = EXTERNAL_DEPENDENCIES
    ET.SubElement(parent, f"{{{NS_MODEL}}}HighLevelSystemDescription").text = HIGH_LEVEL
    ET.SubElement(parent, f"{{{NS_MODEL}}}Owner").text = OWNER
    ET.SubElement(parent, f"{{{NS_MODEL}}}Reviewer").text = REVIEWER
    ET.SubElement(parent, f"{{{NS_MODEL}}}ThreatModelName").text = PROJECT_NAME


def clear_drawing_surface(ds: ET.Element) -> None:
    # Empty the diagram - the canonical DFD ships as Threat Model/ThreatModel.md
    # (Mermaid) and Threat Model/ThreatModel.png (rendered).
    for surface in list(ds):
        for child in list(surface):
            tag = child.tag
            if tag.endswith("Borders") or tag.endswith("Lines"):
                for cell in list(child):
                    child.remove(cell)


def main() -> None:
    if SKELETON is None:
        raise SystemExit(
            "No skeleton .tm7 found. Place a Microsoft TMT-generated .tm7 at"
            f" {OUTPUT} or at the repo root as friend_threatmodel.tm7 and rerun."
        )
    tree = ET.parse(SKELETON)
    root = tree.getroot()

    meta = root.find(f"{{{NS_MODEL}}}MetaInformation")
    build_meta(meta)

    ds = root.find(f"{{{NS_MODEL}}}DrawingSurfaceList")
    clear_drawing_surface(ds)

    ti = root.find(f"{{{NS_MODEL}}}ThreatInstances")
    for child in list(ti):
        ti.remove(child)
    for threat in THREATS:
        ti.append(build_threat_instance(threat))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tree.write(OUTPUT, xml_declaration=False, encoding="utf-8")
    size_kb = OUTPUT.stat().st_size / 1024
    print(f"Wrote {OUTPUT} ({size_kb:.0f} KB) with {len(THREATS)} threats.")


if __name__ == "__main__":
    main()
