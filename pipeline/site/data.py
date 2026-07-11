"""Loads and prepares all content/data JSON for the static site generator.

Pure, read-only, deterministic -- no network access, no AI. Every value
that ends up in a rendered page traces back to a real file under
content/ or data/; this module does no independent fact-generation, only
joining/sorting/formatting what already exists.

Registry-model layout (see CLAUDE.md "Jurisdiction portability" and the P6
migration): loading is split into a jurisdiction-agnostic half and a
per-jurisdiction half, mirroring the split already established across the
rest of /pipeline (see pipeline/ci/validate_content.py's path patterns and
pipeline/audit/run.py's own content_root/data_root split):

  - load_global_data(): config/site.json (the site-wide registry, the
    unified pillar taxonomy, the unified seal vocabulary), the shared
    glossary (content/shared/glossary/*.json -- a term may be referenced by
    more than one jurisdiction's cards, so it lives outside any single
    jurisdiction's tree), and the two data files that stay single, global
    files rather than living under a per-jurisdiction path: data/
    corrections.json (each record carries its own "jurisdiction" field --
    see pipeline/ci/validate_content.py) and data/audit/latest.json (the
    audit loop is not yet jurisdiction-aware -- no audit event carries a
    jurisdiction_id -- matching pipeline/audit/run.py's own comment that
    this file "stays a single global file regardless of --jurisdiction").
  - load_jurisdiction_data(): everything scoped to one jurisdiction id --
    content/<id>/{cards,pillar_states}/*.json, content/<id>/{trajectory,
    document_library,orientation}.json, data/<id>/ledger.json -- validated
    against the pillar/seal vocabulary supplied by load_global_data()
    rather than any jurisdiction-local copy of it.
"""
from __future__ import annotations

import glob
import json
import os


class SiteDataError(Exception):
    """Raised when content that a full build always expects to exist --
    content/<jurisdiction>/orientation.json, content/<jurisdiction>/
    trajectory.json, or a content/<jurisdiction>/pillar_states/*.json file
    for every pillar in config/site.json -- is missing or empty.
    Post-Phase-3 seed content guarantees all of these are present, so a
    missing one is a build error to fail loudly on, not a legitimate
    pre-seed state to degrade gracefully around. Also raised when a
    status_seal or pillar id referenced in content has no matching entry
    in config/site.json's unified pillar/seal vocabulary -- rendering the
    raw internal id to the public site is a worse failure mode than
    refusing to build."""


def _load_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_json_glob(pattern: str) -> list:
    return [_load_json(path) for path in sorted(glob.glob(pattern))]


def _load_json_glob_with_paths(pattern: str) -> list:
    return [(path, _load_json(path)) for path in sorted(glob.glob(pattern))]


def build_timeline_events(cards: list, documents: list, pillar_index: dict) -> list:
    """Merges cards and documents into one ascending-sorted (oldest first,
    left-to-right reading) list of {date, title, url, pillar_names,
    pillar_color_slot, source, status} dicts for the interactive
    timeline ribbon.

    pillar_color_slot is -1 (never 0, a real pillar's slot) for an item
    with no pillar classification -- 0 would fabricate membership in
    whichever pillar happens to be configured first.

    Documents with no published_at are excluded -- a timeline axis has no
    honest way to place an undated point; they still appear, dated or
    not, in the plain Document Library table. Trajectory entries are
    deliberately NOT merged here: their date_or_window values ("2026",
    "H1 2026") are loose windows, not exact dates, and interleaving them
    onto a precise axis as if they were point-in-time would fabricate
    false precision -- they render in a separate rail instead (see
    _timeline.html), never on this list.
    """
    events = []
    for card in cards:
        if not card.get("citations"):
            raise SiteDataError(
                f"content/cards/{card.get('id', '<unknown id>')}.json has an empty or "
                "missing citations array -- every published card must cite at least one "
                "primary source; a card with none must fail the build loudly, not crash "
                "it with an unhandled IndexError or render silently uncited."
            )
        pillars = card.get("pillar") or []
        slot = pillar_index.get(pillars[0], -1) if pillars else -1
        events.append(
            {
                "date": card["published_date"],
                "title": card["title"],
                "url": card["citations"][0]["url"],
                "pillar_names": card.get("pillar_names", []),
                "pillar_color_slot": slot,
                "source": card.get("regulator", ""),
                "status": card.get("status"),
            }
        )
    for doc in documents:
        published_at = doc.get("published_at")
        if not published_at:
            continue
        pillars = doc.get("pillar") or []
        slot = pillar_index.get(pillars[0], -1) if pillars else -1
        events.append(
            {
                "date": published_at[:10],
                "title": doc["title"],
                "url": doc["link"],
                "pillar_names": doc.get("pillar_names", []),
                "pillar_color_slot": slot,
                "source": doc.get("regulator", ""),
                "status": None,
            }
        )
    events.sort(key=lambda e: e["date"])
    return events


def load_global_data(repo_root: str) -> dict:
    """Loads everything a full site build needs that is NOT scoped to a
    single jurisdiction: config/site.json (registry, unified pillars,
    unified seal vocabulary), the shared glossary, and the two data files
    that stay single/global under the registry-model layout (data/
    corrections.json, data/audit/latest.json). See module docstring."""
    site_config = _load_json(os.path.join(repo_root, "config", "site.json"), {})
    pillar_names = {p["id"]: p["name"] for p in site_config.get("pillars", [])}
    # Positional slot (0-6), never a raw pillar-id string, so CSS/JS never
    # hardcode a jurisdiction-specific id -- keeps the timeline's
    # categorical color-by-pillar treatment jurisdiction-portable.
    pillar_index = {p["id"]: i for i, p in enumerate(site_config.get("pillars", []))}
    seal_labels = dict(site_config.get("seal_vocabulary", {}))

    glossary_terms = _load_json_glob(os.path.join(repo_root, "content", "shared", "glossary", "*.json"))
    glossary_terms = sorted((g for g in glossary_terms if g), key=lambda g: g["term"].lower())

    corrections = _load_json(os.path.join(repo_root, "data", "corrections.json"), [])
    audit_latest = _load_json(os.path.join(repo_root, "data", "audit", "latest.json"))

    return {
        "site_config": site_config,
        "pillar_names": pillar_names,
        "pillar_index": pillar_index,
        "seal_labels": seal_labels,
        "glossary_terms": glossary_terms,
        "corrections": corrections,
        "audit_latest": audit_latest,
    }


def load_jurisdiction_data(repo_root: str, jurisdiction_id: str, global_data: dict) -> dict:
    """Loads everything scoped to a single jurisdiction, validated against
    the unified pillar/seal vocabulary in `global_data` (as returned by
    load_global_data()) rather than any jurisdiction-local copy of it."""
    pillar_names = global_data["pillar_names"]
    pillar_index = global_data["pillar_index"]
    seal_labels = global_data["seal_labels"]

    config = _load_json(
        os.path.join(repo_root, "config", "jurisdictions", f"{jurisdiction_id}.json"), {}
    )

    content_root = os.path.join(repo_root, "content", jurisdiction_id)
    data_root = os.path.join(repo_root, "data", jurisdiction_id)

    pillar_state_paths = _load_json_glob_with_paths(os.path.join(content_root, "pillar_states", "*.json"))
    pillar_states = [data for _, data in pillar_state_paths]
    card_paths = _load_json_glob_with_paths(os.path.join(content_root, "cards", "*.json"))
    cards = [data for _, data in card_paths]
    card_source_by_id = {data["id"]: path for path, data in card_paths if data}
    trajectory_path = os.path.join(content_root, "trajectory.json")
    trajectory = _load_json(trajectory_path, [])
    document_library_path = os.path.join(content_root, "document_library.json")
    document_library = _load_json(document_library_path, {"documents": []})
    orientation_path = os.path.join(content_root, "orientation.json")
    orientation = _load_json(orientation_path)
    ledger = _load_json(os.path.join(data_root, "ledger.json"), {"items": {}})

    if not orientation:
        raise SiteDataError(
            f"{orientation_path} is missing or empty -- content/<jurisdiction>/orientation.json "
            "is always-expected seed content post-Phase-3; a build cannot proceed without it."
        )
    if not os.path.exists(trajectory_path):
        raise SiteDataError(
            f"{trajectory_path} is missing -- content/<jurisdiction>/trajectory.json is "
            "always-expected seed content post-Phase-3 (an empty array is a legitimate value, "
            "a missing file is not); a build cannot proceed without it."
        )

    # Pillar order follows config/site.json's unified pillar list, not filesystem glob order.
    pillar_states_by_id = {p["pillar"]: p for p in pillar_states if p}
    pillar_state_path_by_id = {data["pillar"]: path for path, data in pillar_state_paths if data}
    configured_pillar_ids = list(pillar_names.keys())
    missing_pillar_ids = [pid for pid in configured_pillar_ids if pid not in pillar_states_by_id]
    if missing_pillar_ids:
        raise SiteDataError(
            f"content/{jurisdiction_id}/pillar_states/ is missing a state file for pillar id(s): "
            f"{', '.join(missing_pillar_ids)} -- every pillar in config/site.json must have a "
            f"corresponding content/{jurisdiction_id}/pillar_states/*.json post-Phase-3."
        )
    ordered_pillar_states = [pillar_states_by_id[pid] for pid in configured_pillar_ids]
    for state in ordered_pillar_states:
        state["pillar_name"] = pillar_names.get(state["pillar"], state["pillar"])
        if state["status_seal"] not in seal_labels:
            raise SiteDataError(
                f"unmapped status_seal id {state['status_seal']!r} in "
                f"{pillar_state_path_by_id[state['pillar']]} -- add it to seal_vocabulary "
                "in config/site.json or fix the pillar state file."
            )
        state["status_label"] = seal_labels[state["status_seal"]]

    cards = [c for c in cards if c]
    for card in cards:
        unmapped = [p for p in card.get("pillar", []) if p not in pillar_names]
        if unmapped:
            raise SiteDataError(
                f"unmapped pillar id(s) {unmapped} in {card_source_by_id[card['id']]} -- "
                "add them to pillars in config/site.json or fix the card file."
            )
        card["pillar_names"] = [pillar_names[p] for p in card.get("pillar", [])]
    cards.sort(key=lambda c: c["published_date"], reverse=True)

    trajectory = sorted(trajectory or [], key=lambda t: t["date_or_window"])
    for entry in trajectory:
        if entry["pillar"] not in pillar_names:
            raise SiteDataError(
                f"unmapped pillar id {entry['pillar']!r} in {trajectory_path} -- add it to "
                "pillars in config/site.json or fix the trajectory entry."
            )
        entry["pillar_name"] = pillar_names[entry["pillar"]]

    documents = sorted(
        document_library.get("documents", []),
        key=lambda d: d.get("published_at") or "",
        reverse=True,
    )
    for doc in documents:
        unmapped = [p for p in doc.get("pillar", []) if p not in pillar_names]
        if unmapped:
            raise SiteDataError(
                f"unmapped pillar id(s) {unmapped} in {document_library_path} -- add them to "
                "pillars in config/site.json or fix the document entry."
            )
        doc["pillar_names"] = [pillar_names[p] for p in doc.get("pillar", [])]

    timeline_events = build_timeline_events(cards, documents, pillar_index)

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
        "pillar_states": ordered_pillar_states,
        "cards": cards,
        "trajectory": trajectory,
        "documents": documents,
        "timeline_events": timeline_events,
        "orientation": orientation,
        "status_counts": status_counts,
        "ledger_item_count": len(ledger_items),
        "relevant_item_count": len(relevant_items),
    }


def load_site_data(repo_root: str, jurisdiction: str = "hk") -> dict:
    """Temporary scaffolding: calls load_global_data() + load_jurisdiction_data()
    and flattens/merges the two into the exact single-jurisdiction shape
    generate.py's build_site() and every template already expect, so this
    step (P6 plumbing) makes no visible content or navigation change. This
    single-jurisdiction merge -- including the corrections-to-card join
    below, which only makes sense once one jurisdiction's cards are in
    hand -- is explicitly meant to be replaced in the next phase, when
    generate.py itself learns to walk config/site.json's jurisdictions[]
    and render a real multi-jurisdiction site instead of calling this
    wrapper for a single hardcoded id.
    """
    global_data = load_global_data(repo_root)
    jurisdiction_data = load_jurisdiction_data(repo_root, jurisdiction, global_data)

    cards = jurisdiction_data["cards"]

    # Join each correction to its card for a readable title/link on the
    # Method page -- falls back to a reader-appropriate placeholder (never
    # crashes, and never renders the raw 64-char card_id hash -- this page's
    # entire purpose is making corrections legible, CLAUDE.md rule 6) if no
    # matching card is found, e.g. a card that was later removed.
    cards_by_id = {c["id"]: c for c in cards}
    corrections = sorted((global_data["corrections"] or []), key=lambda r: r["corrected_at"], reverse=True)
    for record in corrections:
        matching_card = cards_by_id.get(record["card_id"])
        if matching_card:
            record["card_title"] = matching_card["title"]
        else:
            record["card_title"] = f"Card {record['card_id'][:8]}… (no longer published)"

    return {
        "config": jurisdiction_data["config"],
        "site_name": global_data["site_config"].get("site_name", ""),
        "pillar_names": global_data["pillar_names"],
        "pillar_states": jurisdiction_data["pillar_states"],
        "cards": cards,
        "glossary_terms": global_data["glossary_terms"],
        "trajectory": jurisdiction_data["trajectory"],
        "documents": jurisdiction_data["documents"],
        "timeline_events": jurisdiction_data["timeline_events"],
        "start_here": jurisdiction_data["orientation"],
        "status_counts": jurisdiction_data["status_counts"],
        "ledger_item_count": jurisdiction_data["ledger_item_count"],
        "relevant_item_count": jurisdiction_data["relevant_item_count"],
        "audit_latest": global_data["audit_latest"],
        "corrections": corrections,
    }
