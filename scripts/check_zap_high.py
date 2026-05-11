import json
import sys
from pathlib import Path


def main():
    report_path = Path(sys.argv[1] if len(sys.argv) > 1 else 'reports/zap-report.json')
    if not report_path.exists():
        print(f'ZAP report not found: {report_path}', file=sys.stderr)
        return 1

    report = json.loads(report_path.read_text(encoding='utf-8'))
    high_alerts = []
    for site in report.get('site', []):
        for alert in site.get('alerts', []):
            if int(alert.get('riskcode', 0)) >= 3:
                high_alerts.append(alert.get('alert', 'Unnamed high-risk alert'))

    if high_alerts:
        print('High-risk ZAP alerts found:')
        for alert in sorted(set(high_alerts)):
            print(f'- {alert}')
        return 1

    print('No high-risk ZAP alerts found.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
