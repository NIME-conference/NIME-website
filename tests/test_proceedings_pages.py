"""Tests for the checks that guard the proceedings entry pages generated next to
their PDFs (#89) in scripts/check_site_quality.py. Run with: python3 -m pytest tests
"""
import importlib.util
import os

import pytest
import yaml

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SCRIPTS, f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


csq = load("check_site_quality")


@pytest.fixture(autouse=True)
def clear_problems():
    csq.problems.clear()
    yield
    csq.problems.clear()


def messages(level, check):
    return [m for (lvl, c), msgs in csq.problems.items() if lvl == level and c == check for m in msgs]


def write(path, content="<html></html>"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def manifest(path, files):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump({"files": {p: {"bytes": 1, "sha256": "x"} for p in files}}, f)


def page(url, metas):
    p = csq.PageScanner()
    p.feed("".join(f'<meta name="{k}" content="{v}">' for k, v in metas))
    return p


# --- entry_id_from_url ------------------------------------------------------

@pytest.mark.parametrize("url", [
    "/proc/nime2001_Cook/index.html",
    "/proc/nime2001_cook/",
    "/proceedings/2001/nime2001_cook.html",
])
def test_entry_id_from_either_page_location(url):
    assert csq.entry_id_from_url(url) == "nime2001_cook"


def test_entry_page_regex_matches_both_locations_only():
    assert csq.ENTRY_PAGE.match("/proc/nime2001_cook/index.html")
    assert csq.ENTRY_PAGE.match("/proc_music/nime2026_music_1/index.html")
    assert csq.ENTRY_PAGE.match("/proceedings/2026/nime2026_1.html")
    assert not csq.ENTRY_PAGE.match("/papers/index.html")
    assert not csq.ENTRY_PAGE.match("/proceedings/2026/nime2026_1.pdf")


# --- check_generated_proceedings -------------------------------------------

def test_only_html_may_be_generated_into_proceedings(tmp_path):
    site = tmp_path / "_site"
    write(str(site / "proceedings" / "2026" / "nime2026_1.html"))
    write(str(site / "proceedings" / "2026" / "nime2026_1.pdf"), "%PDF")
    generated = csq.check_generated_proceedings(str(site), str(tmp_path / "missing.yml"))
    assert generated == {"proceedings/2026/nime2026_1.html", "proceedings/2026/nime2026_1.pdf"}
    fails = messages(csq.FAIL, "proceedings")
    assert len(fails) == 1 and "nime2026_1.pdf" in fails[0]


def test_html_on_server_that_the_build_does_not_generate_is_a_warning(tmp_path):
    site = tmp_path / "_site"
    write(str(site / "proceedings" / "2026" / "nime2026_1.html"))
    m = tmp_path / "pdf_manifest.yml"
    manifest(str(m), [
        "proceedings/2026/nime2026_1.pdf",
        "proceedings/2026/nime2026_1.html",        # ours, deployed earlier: fine
        "proceedings/2026/nime2026_99.html",       # entry renamed or removed: stale
        "proceedings/2001/index.php",              # not HTML: not our business
    ])
    csq.check_generated_proceedings(str(site), str(m))
    assert messages(csq.FAIL, "proceedings") == []
    warns = messages(csq.WARN, "proceedings")
    assert len(warns) == 1 and "nime2026_99.html" in warns[0]


def test_clean_build_and_manifest_report_nothing(tmp_path):
    site = tmp_path / "_site"
    write(str(site / "proceedings" / "2001" / "nime2001_cook.html"))
    m = tmp_path / "pdf_manifest.yml"
    manifest(str(m), ["proceedings/2001/nime2001_003.pdf"])
    csq.check_generated_proceedings(str(site), str(m))
    assert not csq.problems


# --- Scholar same-subdirectory rule ----------------------------------------

GOOD = [
    ("citation_title", "T"), ("citation_author", "A"), ("citation_publication_date", "2026"),
    ("citation_conference_title", "NIME"), ("citation_abstract_html_url", "https://nime.org/x"),
]
ENTRY = {"nime2026_1": {"url": "https://nime.org/proceedings/2026/nime2026_1.pdf", "author": "A"}}


def test_moved_page_with_pdf_in_same_directory_passes():
    url = "/proceedings/2026/nime2026_1.html"
    csq.check_scholar(url, page(url, GOOD + [("citation_pdf_url", ENTRY["nime2026_1"]["url"])]), ENTRY)
    assert messages(csq.FAIL, "scholar") == []


@pytest.mark.parametrize("pdf", [
    "https://nime.org/proceedings/2025/nime2026_1.pdf",   # wrong year folder
    "https://nime.org/proceedings/2026/sub/nime2026_1.pdf",  # subfolder
    "https://example.org/proceedings/2026/nime2026_1.pdf",   # other host
])
def test_moved_page_with_pdf_elsewhere_fails(pdf):
    url = "/proceedings/2026/nime2026_1.html"
    csq.check_scholar(url, page(url, GOOD + [("citation_pdf_url", pdf)]), ENTRY)
    fails = messages(csq.FAIL, "scholar")
    assert len(fails) == 1 and "same directory" in fails[0]


def test_legacy_page_is_not_held_to_the_same_directory_rule():
    url = "/proc/nime2026_1/index.html"
    csq.check_scholar(url, page(url, GOOD + [("citation_pdf_url", ENTRY["nime2026_1"]["url"])]), ENTRY)
    assert messages(csq.FAIL, "scholar") == []
