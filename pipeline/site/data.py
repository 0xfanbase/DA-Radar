"""Loads and prepares all content/data JSON for the static site generator.

Pure, read-only, deterministic -- no network access, no AI. Every value
that ends up in a rendered page traces back to a real file under
content/ or data/; this module does no independent fact-generation, only
joining/sorting/formatting what already exists.
"""
from __future__ import annotations

import glob
import json
import os


def _load_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_json_glob(pattern: str) -> list:
    return [_load_json(path) for path in sorted(glob.glob(pattern))]


def load_site_data(repo_root: str) -> dict:
    config = _load_json(os.path.join(repo_root, "config", "jurisdiction.json"), {})
    pillar_names = {p["id"]: p["name"] for p in config.get("pillars", [])}
    seal_labels = {s["id"]: s["label"] for s in config.get("seal_vocabulary", [])}

    pillar_states = _load_json_glob(os.path.join(repo_root, "content", "pillar_states", "*.json"))
    cards = _load_json_glob(os.path.join(repo_root, "content", "cards", "*.json"))
    glossary_terms = _load_json_glob(os.path.join(repo_root, "content", "glossary", "*.json"))
    trajectory = _load_json(os.path.join(repo_root, "content", "trajectory.json"), [])
    document_library = _load_json(
        os.path.join(repo_root, "content", "document_library.json"), {"documents": []}
    )
    start_here = _load_json(os.path.join(repo_root, "content", "start_here.json"))
    ledger = _load_json(os.path.join(repo_root, "data", "ledger.json"), {"items": {}})
    audit_latest = _load_json(os.path.join(repo_root, "data", "audit", "latest.json"))

    # Pillar order follows config/jurisdiction.json, not filesystem glob order.
    pillar_states_by_id = {p["pillar"]: p for p in pillar_states if p}
    ordered_pillar_states = [
        pillar_states_by_id[p["id"]] for p in config.get("pillars", []) if p["id"] in pillar_states_by_id
    ]
    for state in ordered_pillar_states:
        state["pillar_name"] = pillar_names.get(state["pillar"], state["pillar"])
        state["status_label"] = seal_labels.get(state["status_seal"], state["status_seal"])

    cards = [c for c in cards if c]
    for card in cards:
        card["pillar_names"] = [pillar_names.get(p, p) for p in card.get("pillar", [])]
    cards.sort(key=lambda c: c["published_date"], reverse=True)

    trajectory = sorted(trajectory or [], key=lambda t: t["date_or_window"])
    for entry in trajectory:
        entry["pillar_name"] = pillar_names.get(entry["pillar"], entry["pillar"])

    glossary_terms = sorted((g for g in glossary_terms if g), key=lambda g: g["term"].lower())

    documents = sorted(
        document_library.get("documents", []),
        key=lambda d: d.get("published_at") or "",
        reverse=True,
    )
    for doc in documents:
        doc["pillar_names"] = [pillar_names.get(p, p) for p in doc.get("pillar", [])]

    ledger_items = list(ledger.get("items", {}).values())
    relevant_items = [i for i in ledger_items if i.get("relevant", True)]
    # Status counts are scoped to *relevant* items only -- an item's ledger
    # status never leaves "queued" once judged not relevant (there is no
    # "irrelevant"/"suppressed" state in the lifecycle for that), so a raw,
    # unscoped count would conflate "genuinely awaiting analyst attention"
    # with "observed but permanently out of scope." Both figures are shown
    # separately instead of quietly merged into one misleading number.
    status_counts = {}
    for item in relevant_items:
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1

    return {
        "config": config,
        "pillar_names": pillar_names,
        "pillar_states": ordered_pillar_states,
        "cards": cards,
        "glossary_terms": glossary_terms,
        "trajectory": trajectory,
        "documents": documents,
        "start_here": start_here,
        "status_counts": status_counts,
        "ledger_item_count": len(ledger_items),
        "relevant_item_count": len(relevant_items),
        "audit_latest": audit_latest,
    }
