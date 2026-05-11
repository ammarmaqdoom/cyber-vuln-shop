# Executive Summary

Cyber Vuln Shop is a small online shop used to demonstrate secure software delivery. The application supports separate admin and customer roles, product management, cart checkout, and stored order history.

The vulnerable demonstration build exposed ten business and security risks: broken admin access, missing CSRF protection, open redirect, SQL injection, stored XSS, IDOR, debug secret leakage, unauthenticated user dump, unauthenticated database export, and weak password acceptance. The production build remediates these issues and is verified by regression tests plus the GitHub Actions DevSecOps pipeline.

## Business Risk Summary

| Risk Area | Business Impact | Current Status |
| --- | --- | --- |
| Broken RBAC | Normal users could reach admin-only functions if the guard was misused. | Fixed |
| Missing CSRF protection | Attackers could trick logged-in users into submitting unwanted actions. | Fixed |
| Injection and stored XSS | Attackers could leak data through search or execute script through reviews. | Fixed |
| IDOR and bulk export | Attackers could read other customers' orders or download application data. | Fixed |
| No security pipeline | Security findings would not be detected during pushes or PRs. | Fixed |
| No HTTPS demo path | Presentation could fail the deployment baseline. | Fixed |

## Recommendation

Before final presentation, use the successful GitHub Actions run and downloaded artifacts as pipeline evidence, then demonstrate one vulnerable attack and its fixed-app proof live. The current main branch has a passing SAST/SCA/tests/DAST pipeline.
