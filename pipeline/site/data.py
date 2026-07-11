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


class SiteDataError(Exception):
    """Raised when content that a full build always expects to exist --
    content/start_here.json, content/trajectory.json, or a
    content/pillar_states/*.json file for every pillar in
    config/jurisdiction.json -- is missing or empty. Post-Phase-3 seed
    content guarantees all of these are present, so a missing one is a
    build error to fail loudly on, not a legitimate pre-seed state to
    degrade gracefully around. Also raised when a status_seal or pillar id
    referenced in content has no matching entry in config/jurisdiction.json
    -- rendering the raw internal id to the public site is a worse failure
    mode than refusing to build."""


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


def load_site_data(repo_root: str) -> dict:
    config = _load_json(os.path.join(repo_root, "config", "jurisdiction.json"), {})
    pillar_names = {p["id"]: p["name"] for p in config.get("pillars", [])}
    seal_labels = {s["id"]: s["label"] for s in config.get("seal_vocabulary", [])}
    # Positional slot (0-6), never a raw pillar-id string, so CSS/JS never
    # hardcode a jurisdiction-specific id -- keeps the timeline's
    # categorical color-by-pillar treatment jurisdiction-portable.
    pillar_index = {p["id"]: i for i, p in enumerate(config.get("pillars", []))}

    pillar_state_paths = _load_json_glob_with_paths(
        os.path.join(repo_root, "content", "pillar_states", "*.json")
    )
    pillar_states = [data for _, data in pillar_state_paths]
    card_paths = _load_json_glob_with_paths(os.path.join(repo_root, "content", "cards", "*.json"))
    cards = [data for _, data in card_paths]
    card_source_by_id = {data["id"]: path for path, data in card_paths if data}
    glossary_terms = _load_json_glob(os.path.join(repo_root, "content", "glossary", "*.json"))
    trajectory_path = os.path.join(repo_root, "content", "trajectory.json")
    trajectory = _load_json(trajectory_path, [])
    document_library_path = os.path.join(repo_root, "content", "document_library.json")
    document_library = _load_json(document_library_path, {"documents": []})
    start_here_path = os.path.join(repo_root, "content", "start_here.json")
    start_here = _load_json(start_here_path)
    ledger = _load_json(os.path.join(repo_root, "data", "ledger.json"), {"items": {}})
    audit_latest = _load_json(os.path.join(repo_root, "data", "audit", "latest.json"))
    corrections = _load_json(os.path.join(repo_root, "data", "corrections.json"), [])

    if not start_here:
        raise SiteDataError(
            f"{start_here_path} is missing or empty -- content/start_here.json is "
            "always-expected seed content post-Phase-3; a build cannot proceed without it."
        )
    if not os.path.exists(trajectory_path):
        raise SiteDataError(
            f"{trajectory_path} is missing -- content/trajectory.json is always-expected "
            "seed content post-Phase-3 (an empty array is a legitimate value, a missing "
            "file is not); a build cannot proceed without it."
        )

    # Pillar order follows config/jurisdiction.json, not filesystem glob order.
    pillar_states_by_id = {p["pillar"]: p for p in pillar_states if p}
    pillar_state_path_by_id = {data["pillar"]: path for path, data in pillar_state_paths if data}
    configured_pillar_ids = [p["id"] for p in config.get("pillars", [])]
    missing_pillar_ids = [pid for pid in configured_pillar_ids if pid not in pillar_states_by_id]
    if missing_pillar_ids:
        raise SiteDataError(
            "content/pillar_states/ is missing a state file for pillar id(s): "
            f"{', '.join(missing_pillar_ids)} -- every pillar in config/jurisdiction.json "
            "must have a corresponding content/pillar_states/*.json post-Phase-3."
        )
    ordered_pillar_states = [pillar_states_by_id[pid] for pid in configured_pillar_ids]
    for state in ordered_pillar_states:
        state["pillar_name"] = pillar_names.get(state["pillar"], state["pillar"])
        if state["status_seal"] not in seal_labels:
            raise SiteDataError(
                f"unmapped status_seal id {state['status_seal']!r} in "
                f"{pillar_state_path_by_id[state['pillar']]} -- add it to seal_vocabulary "
                "in config/jurisdiction.json or fix the pillar state file."
            )
        state["status_label"] = seal_labels[state["status_seal"]]

    cards = [c for c in cards if c]
    for card in cards:
        unmapped = [p for p in card.get("pillar", []) if p not in pillar_names]
        if unmapped:
            raise SiteDataError(
                f"unmapped pillar id(s) {unmapped} in {card_source_by_id[card['id']]} -- "
                "add them to pillars in config/jurisdiction.json or fix the card file."
            )
        card["pillar_names"] = [pillar_names[p] for p in card.get("pillar", [])]
    cards.sort(key=lambda c: c["published_date"], reverse=True)

    trajectory = sorted(trajectory or [], key=lambda t: t["date_or_window"])
    for entry in trajectory:
        if entry["pillar"] not in pillar_names:
            raise SiteDataError(
                f"unmapped pillar id {entry['pillar']!r} in {trajectory_path} -- add it to "
                "pillars in config/jurisdiction.json or fix the trajectory entry."
            )
        entry["pillar_name"] = pillar_names[entry["pillar"]]

    glossary_terms = sorted((g for g in glossary_terms if g), key=lambda g: g["term"].lower())

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
                "pillars in config/jurisdiction.json or fix the document entry."
            )
        doc["pillar_names"] = [pillar_names[p] for p in doc.get("pillar", [])]

    timeline_events = build_timeline_events(cards, documents, pillar_index)

    # Join each correction to its card for a readable title/link on the
    # Method page -- falls back to a reader-appropriate placeholder (never
    # crashes, and never renders the raw 64-char card_id hash -- this page's
    # entire purpose is making corrections legible, CLAUDE.md rule 6) if no
    # matching card is found, e.g. a card that was later removed.
    cards_by_id = {c["id"]: c for c in cards}
    corrections = sorted((corrections or []), key=lambda r: r["corrected_at"], reverse=True)
    for record in corrections:
        matching_card = cards_by_id.get(record["card_id"])
        if matching_card:
            record["card_title"] = matching_card["title"]
        else:
            record["card_title"] = f"Card {record['card_id'][:8]}… (no longer published)"

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
        "timeline_events": timeline_events,
        "start_here": start_here,
        "status_counts": status_counts,
        "ledger_item_count": len(ledger_items),
        "relevant_item_count": len(relevant_items),
        "audit_latest": audit_latest,
        "corrections": corrections,
    }
