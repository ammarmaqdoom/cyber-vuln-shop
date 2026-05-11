# Executive Summary

Cyber Vuln Shop is a small online shop used to demonstrate secure software delivery. The application supports separate admin and customer roles, product management, cart checkout, and stored order history.

The original implementation had several business and security risks that could affect grading and real users: broken startup imports, unreliable admin authorization, missing cart database models, missing CSRF protection, incomplete CRUD pages, and no automated security pipeline. These issues were remediated before submission.

## Business Risk Summary

| Risk Area | Business Impact | Current Status |
| --- | --- | --- |
| Broken RBAC | Normal users could reach admin-only functions if the guard was misused. | Fixed |
| Missing CSRF protection | Attackers could trick logged-in users into submitting unwanted actions. | Fixed |
| Broken cart/checkout | Users could not reliably buy products or prove database persistence. | Fixed |
| No security pipeline | Security findings would not be detected during pushes or PRs. | Fixed |
| No HTTPS demo path | Presentation could fail the deployment baseline. | Fixed |

## Recommendation

Before final presentation, run the GitHub Actions workflow, download the artifacts, and add screenshots of the passing pipeline plus one live DAST/pentest demonstration to the slide deck. Use the issue-linked commit format required by the course for every remaining push.
