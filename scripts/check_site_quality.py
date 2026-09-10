#!/usr/bin/env python3
"""SEO / discoverability checks for the built NIME site (_site).

Run after `bundle exec jekyll build`. Exit code 1 if any FAIL is found.

Checks:
  data     - bibliography YAML in _data: duplicate IDs (case-insensitive), malformed
             author strings, PDF URLs with whitespace or non-https scheme.
  pages    - every HTML page: non-empty <title>, non-empty meta description,
             exactly one <h1>, rel=canonical, no duplicate id= attributes,
             every <iframe> has a title.
  scholar  - every proceedings page (/proc*/): Google Scholar "Highwire" tags
             citation_title, citation_author (>=1, no stray "and"),
             citation_publication_date, citation_conference_title,
             citation_pdf_url (non-empty when the entry has a url) and
             citation_doi when the entry has a DOI.
  sitemap  - every <loc> in sitemap.xml resolves to a file in _site (case-sensitive),
             the 404 page is not listed, no mixed-case paths.

Warnings are printed but do not fail the build; pass --strict to make them fail.
"""
import argparse
import glob
import html
import os
import re
import sys
from collections import Counter, defaultdict
from html.parser import HTMLParser

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

FAIL, WARN = "FAIL", "WARN"
problems = defaultdict(list)  # (level, check) -> [messages]


def report(level, check, msg):
    problems[(level, check)].append(msg)


class PageScanner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self.in_title = False
        self.metas = defaultdict(list)
        self.links = defaultdict(list)
        self.ids = Counter()
        self.h1 = 0
        self.iframes_without_title = 0
        self.imgs_without_alt = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.in_title = True
            self.title = ""
        elif tag == "meta" and a.get("name"):
            self.metas[a["name"]].append(a.get("content", ""))
        elif tag == "link" and a.get("rel"):
            self.links[a["rel"]].append(a.get("href", ""))
        elif tag == "h1":
            self.h1 += 1
        elif tag == "iframe" and not (a.get("title") or "").strip():
            self.iframes_without_title += 1
        elif tag == "img" and "alt" not in a:
            self.imgs_without_alt += 1
        if a.get("id"):
            self.ids[a["id"]] += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def rel(path, site):
    return "/" + os.path.relpath(path, site).replace(os.sep, "/")


def check_data(data_dir):
    if yaml is None:
        report(WARN, "data", "PyYAML not installed; skipping bibliography data checks")
        return {}
    entries_by_id = {}
    for f in sorted(glob.glob(os.path.join(data_dir, "nime_*.yaml"))):
        name = os.path.basename(f)
        entries = yaml.safe_load(open(f, encoding="utf-8")) or []
        seen = Counter(e["ID"].lower() for e in entries if e.get("ID"))
        for key, n in seen.items():
            if n > 1:
                report(FAIL, "data", f"{name}: ID '{key}' appears {n} times (case-insensitive); "
                                     "only one page will be generated")
        for e in entries:
            eid = e.get("ID", "?")
            entries_by_id[eid.lower()] = e
            author = e.get("author", "") or ""
            if not author.strip():
                report(WARN, "data", f"{name}:{eid}: empty author field")
            elif re.search(r"(^\s*and\b|\band\s*$|,\s*and\b|\band\s*,)", author):
                report(WARN, "data", f"{name}:{eid}: suspicious author string: {author!r}")
            url = e.get("url", "") or ""
            if url and re.search(r"\s", url):
                report(FAIL, "data", f"{name}:{eid}: PDF url contains whitespace: {url!r}")
            elif url and not url.startswith("https://"):
                report(WARN, "data", f"{name}:{eid}: PDF url is not https: {url}")
            if not url and not e.get("doi"):
                report(WARN, "data", f"{name}:{eid}: entry has neither url nor doi")
            if not (e.get("abstract") or "").strip():
                report(WARN, "data", f"{name}:{eid}: no abstract")
    return entries_by_id


def check_pages(site, entries_by_id):
    pages = sorted(glob.glob(os.path.join(site, "**", "*.html"), recursive=True))
    for path in pages:
        url = rel(path, site)
        if "/web_archive/" in url or "/proceedings/" in url:
            continue
        p = PageScanner()
        p.feed(open(path, encoding="utf-8", errors="replace").read())
        is_404 = os.path.basename(path) == "404.html" or url.startswith("/404/")

        if not (p.title or "").strip():
            report(FAIL, "pages", f"{url}: empty <title>")
        desc = " ".join(p.metas.get("description", [""])).strip()
        if not desc and not is_404:
            report(FAIL, "pages", f"{url}: empty meta description")
        if p.h1 != 1 and not is_404:
            report(FAIL, "pages", f"{url}: expected exactly one <h1>, found {p.h1}")
        if not p.links.get("canonical") and not is_404:
            report(FAIL, "pages", f"{url}: missing <link rel=\"canonical\">")
        for i, n in p.ids.items():
            if n > 1:
                report(FAIL, "pages", f"{url}: duplicate id attribute '{i}' ({n}x)")
        if p.iframes_without_title:
            report(FAIL, "pages", f"{url}: {p.iframes_without_title} <iframe> without title")
        if p.imgs_without_alt:
            report(FAIL, "pages", f"{url}: {p.imgs_without_alt} <img> without alt attribute")

        if re.match(r"^/proc(_[a-z]+)?/", url):
            check_scholar(url, p, entries_by_id)


def check_scholar(url, p, entries_by_id):
    m = p.metas
    eid = re.sub(r"/index\.html$", "", url).rstrip("/").split("/")[-1].lower()
    entry = entries_by_id.get(eid, {})

    if not any(x.strip() for x in m.get("citation_title", [])):
        report(FAIL, "scholar", f"{url}: missing citation_title")
    authors = [a for a in m.get("citation_author", []) if a.strip()]
    if not authors:
        if entry.get("author"):
            report(FAIL, "scholar", f"{url}: no citation_author tags")
        else:
            report(WARN, "scholar", f"{url}: entry has no author field (fix in NIME-bibliography)")
    for a in authors:
        if re.search(r"(^\s*and\b|\band\s*$|\band\s*,|,\s*and\b)", a):
            report(WARN, "scholar", f"{url}: citation_author looks malformed: {a!r}")
    if not any(re.match(r"^\d{4}", x.strip()) for x in m.get("citation_publication_date", [])):
        report(FAIL, "scholar", f"{url}: citation_publication_date missing or not YYYY[/MM/DD]")
    if not any(x.strip() for x in m.get("citation_conference_title", [])):
        report(FAIL, "scholar", f"{url}: missing citation_conference_title")

    pdf = [x for x in m.get("citation_pdf_url", []) if x.strip()]
    fulltext = [x for x in m.get("citation_fulltext_html_url", []) if x.strip()]
    if entry.get("url") and not pdf and not fulltext:
        report(FAIL, "scholar", f"{url}: no citation_pdf_url / citation_fulltext_html_url although entry has a url")
    if not entry.get("url") and not pdf and not fulltext:
        report(WARN, "scholar", f"{url}: no full-text link (entry has no url or doi); Scholar needs one")
    for x in pdf:
        if not x.startswith("https://"):
            report(WARN, "scholar", f"{url}: citation_pdf_url is not https: {x}")
        if "doi.org/" in x or "pubpub.org/" in x:
            report(WARN, "scholar", f"{url}: citation_pdf_url points at an HTML landing page, not a PDF: {x}")
    for x in fulltext:
        if not x.startswith("https://"):
            report(WARN, "scholar", f"{url}: citation_fulltext_html_url is not https: {x}")

    if entry.get("doi") and not any(x.strip() for x in m.get("citation_doi", [])):
        report(FAIL, "scholar", f"{url}: entry has a DOI but no citation_doi tag")
    if not m.get("citation_abstract_html_url"):
        report(WARN, "scholar", f"{url}: missing citation_abstract_html_url (should be the page's own URL)")


def check_sitemap(site):
    sm = os.path.join(site, "sitemap.xml")
    if not os.path.exists(sm):
        report(FAIL, "sitemap", "sitemap.xml not generated")
        return
    text = open(sm, encoding="utf-8").read()
    locs = [html.unescape(x) for x in re.findall(r"<loc>([^<]+)</loc>", text)]
    if not locs:
        report(FAIL, "sitemap", "sitemap.xml lists no URLs")
    for loc in locs:
        path = re.sub(r"^https?://[^/]+", "", loc)
        if path.rstrip("/") in ("/404", "/404.html"):
            report(FAIL, "sitemap", f"{loc}: the 404 page should not be in the sitemap (add sitemap: false)")
        fs = os.path.join(site, path.lstrip("/"))
        if path.endswith("/"):
            fs = os.path.join(fs, "index.html")
        if not os.path.exists(fs):
            report(FAIL, "sitemap", f"{loc}: no such file in _site (case-sensitive)")
        if path != path.lower():
            report(WARN, "sitemap", f"{loc}: mixed-case URL; keep permalinks lowercase")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="_site")
    ap.add_argument("--data", default="_data")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    ap.add_argument("--max-print", type=int, default=25, help="messages to print per check")
    args = ap.parse_args()

    entries = check_data(args.data)
    check_pages(args.site, entries)
    check_sitemap(args.site)

    exit_code = 0
    for level in (FAIL, WARN):
        for (lvl, check), msgs in sorted(problems.items()):
            if lvl != level:
                continue
            print(f"\n== {lvl} [{check}] {len(msgs)} issue(s)")
            for m in msgs[: args.max_print]:
                print("  -", m)
            if len(msgs) > args.max_print:
                print(f"  ... and {len(msgs) - args.max_print} more")
            if lvl == FAIL or (lvl == WARN and args.strict):
                exit_code = 1
    if not problems:
        print("All site quality checks passed.")
    print(f"\nSummary: {sum(len(v) for (l, _), v in problems.items() if l == FAIL)} failures, "
          f"{sum(len(v) for (l, _), v in problems.items() if l == WARN)} warnings")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
