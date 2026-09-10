#!/usr/bin/env python3
"""Build a pa11y-ci config from the generated sitemap.

Every non-proceedings page is tested. Proceedings pages are all built from the
same layout, so a sample is enough: the first N of each type plus the newest year.
"""
import json
import os
import re
import sys

site = sys.argv[1] if len(sys.argv) > 1 else "_site"
base = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5089"
per_type = int(os.environ.get("PA11Y_PROC_SAMPLE", "3"))

text = open(os.path.join(site, "sitemap.xml"), encoding="utf-8").read()
paths = [re.sub(r"^https?://[^/]+", "", l) for l in re.findall(r"<loc>([^<]+)</loc>", text)]

urls, per_dir = [], {}
for p in sorted(paths):
    m = re.match(r"^/(proc(?:_[a-z]+)?)/", p)
    if not m:
        urls.append(p)
        continue
    d = m.group(1)
    per_dir.setdefault(d, [])
    per_dir[d].append(p)
for d, ps in per_dir.items():
    urls += ps[:per_type] + ps[-per_type:]
urls.append("/404.html")

config = {
    "defaults": {
        "standard": "WCAG2AA",
        "runners": ["axe", "htmlcs"],
        # /papers/ is a 1.1 MB page with ~2500 list items; axe + htmlcs take
        # about a minute on it locally and longer on a CI runner. A timeout
        # kills the browser and fails every page queued after it.
        "timeout": 300000,
        "wait": 500,
        # With concurrency > 1 pa11y-ci shares one Chrome and every second
        # page dies with "Connection closed" on the GitHub runner.
        "concurrency": 1,
        "chromeLaunchConfig": {"args": ["--no-sandbox", "--disable-dev-shm-usage"]},
        # axe cannot inspect cross-origin iframes (YouTube embeds) and reports
        # "frame-tested" as an error for every one; the frame itself is not ours.
        "ignore": ["frame-tested"],
    },
    "urls": [base + u for u in dict.fromkeys(urls)],
}
json.dump(config, sys.stdout, indent=2)
print()
