#!/usr/bin/env python3
"""Write the summary email from the calculations, to the picked recipients.

Usage: compose_email.py <email.md>
Output (flow): {"to": "a@x.com, b@y.com", "to_list": [...], "subject": ..., "body": ..., "file": <email.md>}
"""
import sys

from flow import flow

out = sys.argv[1]
c = flow.steps["calculate"].json
to = [a.strip() for a in flow.inputs.get("recipients", "").splitlines() if a.strip()]
if not to:
    sys.exit("no recipients picked")
bad = [a for a in to if "@" not in a or " " in a]
if bad:
    sys.exit(f"not email addresses: {', '.join(bad)}")

subject = f"Orders report: {c['base']}"
period = f" ({c['from']} to {c['to']})" if c.get("from") else ""
body = f"""Hi,

Here are the totals for {c['base']}{period}:

- Revenue: ${c['revenue']:,.2f}
- Orders: {c['orders']}
- Units: {c['units']}
- Average order: ${c['average']:,.2f}
- Top category: {c['top_category']}
- Top product: {c['top_product']}

The full breakdown by category, state and product is in the reports folder on Drive.
"""
with open(out, "w") as f:
    f.write(f"To: {', '.join(to)}\nSubject: {subject}\n\n{body}")
print(f"to {', '.join(to)}: {subject}")
flow.set_output({"to": ", ".join(to), "to_list": to, "subject": subject, "body": body, "file": out})
