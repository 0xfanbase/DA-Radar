"""Tests for pipeline.ci.apply_verification_gate -- wiring the
non-bypassable gate to real files on disk."""
from __future__ import annotations

import json
import subprocess

from pipeline.ci.apply_verification_gate import apply_gate_to_file, main

UA = "TestAgent/0.1"
FETCH_KWARGS = dict(
    timeout=5, max_retries=3, backoff_base=0.01, backoff_multiplier=2.0, official_domains=["example.invalid"]
)
DOC_URL = "https://example.invalid/doc"


def _card(status="verified", quote="takes effect on 1 August 2026", url=DOC_URL):
    return {
        "schema_version": 1,
        "id": "card-1",
        "published_date": "2026-01-01",
        "regulator": "Example Regulator",
        "pillar": ["example_pillar"],
        "type": "circular",
        "title": "t",
        "summary": "s",
        "why_it_matters": "w",
        "citations": [{"url": url, "quote": quote}],
        "status": status,
        "generated_at": "2026-01-01T00:00:00Z",
        "model": "test-model",
    }


def _init_repo(repo_dir):
    subprocess.run(["git", "-c", "commit.gpgsign=false", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo_dir, check=True)


def _commit_all(repo_dir, message):
    subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo_dir, check=True)


def test_apply_gate_to_file_leaves_authentic_card_unchanged(tmp_path, requests_mock, fixture_bytes):
    requests_mock.get(DOC_URL, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"})
    path = tmp_path / "card.json"
    path.write_text(json.dumps(_card(status="verified")))

    changed = apply_gate_to_file(str(path), user_agent=UA, **FETCH_KWARGS)

    assert changed is False
    assert json.loads(path.read_text())["status"] == "verified"


def test_apply_gate_to_file_downgrades_fabricated_card(tmp_path, requests_mock, fixture_bytes):
    requests_mock.get(DOC_URL, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"})
    path = tmp_path / "card.json"
    path.write_text(json.dumps(_card(status="verified", quote="licence revoked with immediate effect")))

    changed = apply_gate_to_file(str(path), user_agent=UA, **FETCH_KWARGS)

    assert changed is True
    assert json.loads(path.read_text())["status"] == "unverified"


def test_main_processes_only_uncommitted_card_files(tmp_path, requests_mock, fixture_bytes):
    _init_repo(tmp_path)
    (tmp_path / "content" / "hk" / "cards").mkdir(parents=True)
    (tmp_path / "content" / "hk" / "cards" / "README.txt").write_text("not a card")
    _commit_all(tmp_path, "base")

    requests_mock.get(DOC_URL, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"})
    card_path = tmp_path / "content" / "hk" / "cards" / "card-1.json"
    card_path.write_text(json.dumps(_card(status="verified", quote="licence revoked with immediate effect")))

    exit_code = main(["--repo-dir", str(tmp_path), "--user-agent", UA])

    assert exit_code == 0
    assert json.loads(card_path.read_text())["status"] == "unverified"


def test_main_with_no_changed_cards_is_a_noop(tmp_path):
    _init_repo(tmp_path)
    exit_code = main(["--repo-dir", str(tmp_path)])
    assert exit_code == 0


def test_main_downgrades_card_whose_citation_domain_is_missing_from_config(tmp_path, requests_mock, fixture_bytes):
    """main() derives official_domains from <repo-dir>/config/jurisdiction.json
    itself -- a citation to a domain absent from that config is a hard
    failure at the real CI entrypoint, not just in the in-memory gate."""
    _init_repo(tmp_path)
    (tmp_path / "content" / "hk" / "cards").mkdir(parents=True)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "jurisdiction.json").write_text(
        json.dumps({"regulators": [{"id": "x", "official_domains": ["www.official.invalid"]}]})
    )
    _commit_all(tmp_path, "base")

    requests_mock.get(DOC_URL, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"})
    card_path = tmp_path / "content" / "hk" / "cards" / "card-1.json"
    card_path.write_text(json.dumps(_card(status="verified")))

    exit_code = main(["--repo-dir", str(tmp_path), "--user-agent", UA])

    assert exit_code == 0
    assert json.loads(card_path.read_text())["status"] == "unverified"


def test_main_leaves_card_verified_when_citation_domain_is_in_config(tmp_path, requests_mock, fixture_bytes):
    _init_repo(tmp_path)
    (tmp_path / "content" / "hk" / "cards").mkdir(parents=True)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "jurisdiction.json").write_text(
        json.dumps({"regulators": [{"id": "x", "official_domains": ["example.invalid"]}]})
    )
    _commit_all(tmp_path, "base")

    requests_mock.get(DOC_URL, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"})
    card_path = tmp_path / "content" / "hk" / "cards" / "card-1.json"
    card_path.write_text(json.dumps(_card(status="verified")))

    exit_code = main(["--repo-dir", str(tmp_path), "--user-agent", UA])

    assert exit_code == 0
    assert json.loads(card_path.read_text())["status"] == "verified"


def test_apply_gate_to_file_downgrades_over_limit_quote(tmp_path, requests_mock, fixture_bytes):
    requests_mock.get(DOC_URL, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"})
    long_quote = " ".join(f"word{i}" for i in range(16))
    path = tmp_path / "card.json"
    path.write_text(json.dumps(_card(status="verified", quote=long_quote)))

    changed = apply_gate_to_file(str(path), user_agent=UA, **FETCH_KWARGS)

    assert changed is True
    assert json.loads(path.read_text())["status"] == "unverified"


def test_apply_gate_to_file_downgrades_duplicate_citation_urls(tmp_path, requests_mock, fixture_bytes):
    requests_mock.get(DOC_URL, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"})
    card = _card(status="verified")
    card["citations"] = [
        {"url": DOC_URL, "quote": "takes effect on 1 August 2026"},
        {"url": DOC_URL, "quote": "takes effect on 1 August 2026"},
    ]
    path = tmp_path / "card.json"
    path.write_text(json.dumps(card))

    changed = apply_gate_to_file(str(path), user_agent=UA, **FETCH_KWARGS)

    assert changed is True
    assert json.loads(path.read_text())["status"] == "unverified"


def test_apply_gate_to_file_writes_numeric_claims_unsupported_field(tmp_path, requests_mock, fixture_bytes):
    """apply_gate_to_file now calls enforce_full_gate, not just
    enforce_verification_gate -- a numeric claim that doesn't trace to
    the fetched source must get written to disk as
    numeric_claims_unsupported, alongside the status downgrade."""
    requests_mock.get(DOC_URL, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"})
    card = _card(status="verified")
    card["summary"] = "Capital requirements are set at HK$99 million."
    path = tmp_path / "card.json"
    path.write_text(json.dumps(card))

    changed = apply_gate_to_file(str(path), user_agent=UA, **FETCH_KWARGS)

    assert changed is True
    on_disk = json.loads(path.read_text())
    assert on_disk["status"] == "unverified"
    assert on_disk["numeric_claims_unsupported"] == ["HK$99 million"]
