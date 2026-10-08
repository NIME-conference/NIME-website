"""Tests for the PDF manifest (scripts/make_pdf_manifest.py) and its checks
in scripts/check_site_quality.py. Run with: python3 -m pytest tests
"""
import hashlib
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


make = load("make_pdf_manifest")
csq = load("check_site_quality")


@pytest.fixture(autouse=True)
def clear_problems():
    csq.problems.clear()
    yield
    csq.problems.clear()


def write(path, content=b"%PDF-1.4\n"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)


def messages(level):
    return [m for (lvl, check), msgs in csq.problems.items()
            if lvl == level and check == "pdfs" for m in msgs]


def entry(eid, url):
    return ("nime_papers.yaml", {"ID": eid, "url": url})


def manifest_file(tmp_path, files):
    path = tmp_path / "pdf_manifest.yml"
    path.write_text(make.to_yaml(files, "2026-10-08T00:00:00Z"), encoding="utf-8")
    return str(path)


# make_pdf_manifest.py

def test_scan_lists_files_with_size_and_hash(tmp_path):
    write(tmp_path / "proceedings" / "2026" / "nime2026_1.pdf", b"abc")
    write(tmp_path / "proceedings" / "2001" / "Bowen.pdf", b"hello")
    files = make.scan(str(tmp_path))
    assert files == {
        "proceedings/2001/Bowen.pdf": {"bytes": 5, "sha256": hashlib.sha256(b"hello").hexdigest()},
        "proceedings/2026/nime2026_1.pdf": {"bytes": 3, "sha256": hashlib.sha256(b"abc").hexdigest()},
    }


def test_scan_skips_dotfiles_and_dot_directories(tmp_path):
    write(tmp_path / "proceedings" / "2026" / "a.pdf")
    write(tmp_path / "proceedings" / "2026" / ".DS_Store")
    write(tmp_path / "proceedings" / ".git" / "HEAD")
    assert list(make.scan(str(tmp_path))) == ["proceedings/2026/a.pdf"]


def test_scan_missing_folder_is_an_error(tmp_path):
    with pytest.raises(SystemExit):
        make.scan(str(tmp_path))


def test_yaml_round_trips_including_awkward_names(tmp_path):
    files = {
        "proceedings/2019/nime2019_music00I.pdf": {"bytes": 1, "sha256": "aa"},
        "proceedings/2004/a file: with 'quotes' #1.pdf": {"bytes": 2, "sha256": "bb"},
    }
    data = yaml.safe_load(make.to_yaml(files, "2026-10-08T00:00:00Z"))
    assert data["files"] == files
    assert data["count"] == 2


# check_site_quality.py: check_manifest

def test_no_manifest_warns_once_and_skips(tmp_path):
    csq.check_manifest(str(tmp_path / "missing.yml"),
                       [entry("nime2026_1", "https://nime.org/proceedings/2026/nime2026_1.pdf")])
    assert messages(csq.FAIL) == []
    assert len(messages(csq.WARN)) == 1


def test_present_small_pdf_passes(tmp_path):
    m = manifest_file(tmp_path, {"proceedings/2026/nime2026_1.pdf": {"bytes": 100, "sha256": "x"}})
    csq.check_manifest(m, [entry("nime2026_1", "https://nime.org/proceedings/2026/nime2026_1.pdf")])
    assert csq.problems == {}


def test_missing_pdf_fails(tmp_path):
    # The case behind #79: the bibliography points at files that were never uploaded.
    m = manifest_file(tmp_path, {})
    csq.check_manifest(m, [entry("nime2020_music1", "https://www.nime.org/proceedings/2020/music1.pdf")])
    assert len(messages(csq.FAIL)) == 1
    assert "proceedings/2020/music1.pdf" in messages(csq.FAIL)[0]


def test_case_mismatch_fails_with_a_hint(tmp_path):
    m = manifest_file(tmp_path, {"proceedings/2019/nime2019_music00I.pdf": {"bytes": 1, "sha256": "x"}})
    csq.check_manifest(m, [entry("x", "https://nime.org/proceedings/2019/nime2019_music00i.pdf")])
    [fail] = messages(csq.FAIL)
    assert "nime2019_music00I.pdf" in fail and "case" in fail
    assert messages(csq.WARN) == []  # the server file is accounted for, so not an orphan too


def test_www_and_http_urls_map_to_the_same_file(tmp_path):
    m = manifest_file(tmp_path, {"proceedings/2010/a.pdf": {"bytes": 1, "sha256": "x"},
                                 "proceedings/2010/b.pdf": {"bytes": 1, "sha256": "x"}})
    csq.check_manifest(m, [entry("a", "http://www.nime.org/proceedings/2010/a.pdf"),
                           entry("b", "https://nime.org/proceedings/2010/b.pdf")])
    assert csq.problems == {}


def test_percent_encoded_url_matches_the_file_name(tmp_path):
    m = manifest_file(tmp_path, {"proceedings/2005/my paper.pdf": {"bytes": 1, "sha256": "x"}})
    csq.check_manifest(m, [entry("a", "https://nime.org/proceedings/2005/my%20paper.pdf")])
    assert csq.problems == {}


@pytest.mark.parametrize("size, warned", [
    (5_000_000, False),
    (5_000_001, True),
    (5 * 1024 * 1024, True),  # 5 MiB is over the limit we use
])
def test_size_limit(tmp_path, size, warned):
    m = manifest_file(tmp_path, {"proceedings/2026/big.pdf": {"bytes": size, "sha256": "x"}})
    csq.check_manifest(m, [entry("big", "https://nime.org/proceedings/2026/big.pdf")])
    assert messages(csq.FAIL) == []
    assert (len(messages(csq.WARN)) == 1) == warned


def test_unreferenced_pdf_warns_but_other_files_do_not(tmp_path):
    m = manifest_file(tmp_path, {"proceedings/2026/orphan.pdf": {"bytes": 1, "sha256": "x"},
                                 "proceedings/2026/video.mp4": {"bytes": 1, "sha256": "x"}})
    csq.check_manifest(m, [])
    [warn] = messages(csq.WARN)
    assert "orphan.pdf" in warn


def test_entries_off_nime_org_are_ignored(tmp_path):
    m = manifest_file(tmp_path, {})
    csq.check_manifest(m, [entry("a", "https://doi.org/10.5281/zenodo.1"),
                           entry("b", "https://nime.pubpub.org/pub/abc"),
                           entry("c", ""),
                           ("nime_music.yaml", {"ID": "d"})])
    assert csq.problems == {}


def test_check_data_returns_every_entry_for_the_manifest_check(tmp_path):
    (tmp_path / "nime_papers.yaml").write_text(
        "- ID: a\n  url: https://nime.org/proceedings/2026/a.pdf\n"
        "- ID: A\n  url: https://nime.org/proceedings/2026/A.pdf\n", encoding="utf-8")
    entries_by_id, all_entries = csq.check_data(str(tmp_path))
    assert len(entries_by_id) == 1  # duplicate IDs collapse here (and FAIL in the data check)...
    assert [e["ID"] for _, e in all_entries] == ["a", "A"]  # ...but both PDFs are still checked
