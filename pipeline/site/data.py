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
import re


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


# Recognized section headers inside a jurisdiction's orientation.json
# "body" free-text field (see pipeline/schemas/orientation.json -- prose
# paragraphs separated by blank lines, with a small fixed set of headers
# the analyst is expected to reuse across jurisdictions so the Current
# State page can find "How to use this site" mechanically, by header text,
# rather than by position or jurisdiction id). Shared with
# split_orientation_body() below and, previously, duplicated inline in
# current_state.html -- kept in exactly one place now.
_ORIENTATION_KNOWN_HEADERS = [
    "Who regulates what",
    "The two regimes already in force",
    "What is coming next",
    "How to use this site",
]

# The one section, if present, that becomes a jurisdiction's "New here?
# How to read this board" panel notes (see current_state.html) instead of
# rendering inline in the full orientation essay -- this is the literal
# mechanism behind "sourced from the jurisdiction's own orientation.json
# for the per-jurisdiction reading notes" (P7 plan): whichever
# jurisdiction's orientation.json carries this header, that section
# becomes its panel's notes. No jurisdiction id is ever compared here.
_ORIENTATION_PANEL_HEADER = "How to use this site"

# Shared, jurisdiction-invariant prose explaining what each status seal
# means in plain English -- the "seal_legend_copy" the P7 plan calls for,
# rendered in the same "New here?" panel as the per-jurisdiction notes
# above. Keyed by config/site.json's seal_vocabulary ids (unified across
# every jurisdiction, see CLAUDE.md's Jurisdiction portability section),
# never a jurisdiction id, so this same dict serves every jurisdiction
# without change. A seal id with no entry here (e.g. a future jurisdiction
# introduces a new seal_vocabulary id before this dict is updated) simply
# renders with no description in the legend -- degrades gracefully rather
# than raising, since the seal itself still renders correctly everywhere
# else on the site either way.
SEAL_LEGEND_COPY = {
    "in_force": (
        "A licensing or supervisory regime for this pillar already has legal effect -- "
        "the rules described are being applied today, not merely proposed."
    ),
    "consultation_open": (
        "A regulator has published a proposal for this pillar and is currently accepting "
        "public comment; the rules described are not yet final."
    ),
    "bill_pending": (
        "A consultation on this pillar has concluded and legislation to implement the "
        "resulting regime has been announced or introduced, but has not yet passed into law."
    ),
    "proposed": (
        "A regulator or government body has signalled an intention to regulate this pillar, "
        "without yet opening a formal public consultation."
    ),
    "no_dedicated_regime": (
        "No licensing or supervisory regime specific to this pillar exists yet in this "
        "jurisdiction."
    ),
}


def split_orientation_body(body: str) -> dict:
    """Splits a jurisdiction's orientation.json "body" field into the two
    views the Current State page renders it as:

      - "essay_items": every paragraph EXCEPT the "How to use this site"
        section, as an ordered list of {"is_heading": bool, "text": str}
        -- exactly what the page's full orientation essay renders (a
        lead-in paragraph or two under no heading, then each recognized
        section). Replaces what used to be inline header-matching Jinja
        logic in current_state.html with one implementation, used by both
        the essay and the panel below.
      - "panel_notes": the "How to use this site" section's own
        paragraphs (list of str, usually one), used as the per-
        jurisdiction reading notes inside the "New here? How to read this
        board" panel -- pulled out of the essay so the same text isn't
        rendered twice on one page.

    A body with no recognized headers at all (e.g. a hand-written test
    fixture, or a not-yet-fully-conformant future jurisdiction) degrades
    gracefully: every paragraph lands in "essay_items" under no heading,
    "panel_notes" comes back empty, and the panel simply shows the shared
    seal legend on its own -- never a crash, never a fabricated notes
    paragraph.
    """
    essay_items = []
    panel_notes = []
    in_panel_section = False
    for para in (body or "").split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if para in _ORIENTATION_KNOWN_HEADERS:
            in_panel_section = para == _ORIENTATION_PANEL_HEADER
            if not in_panel_section:
                essay_items.append({"is_heading": True, "text": para})
            continue
        if in_panel_section:
            panel_notes.append(para)
        else:
            essay_items.append({"is_heading": False, "text": para})
    return {"essay_items": essay_items, "panel_notes": panel_notes}


_EXACT_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_YEAR_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")
_QUARTER_RE = re.compile(r"^(?:Q([1-4])\s+(\d{4})|(\d{4})\s+Q([1-4]))$", re.IGNORECASE)
_HALF_RE = re.compile(r"^(?:H([1-2])\s+(\d{4})|(\d{4})\s+H([1-2]))$", re.IGNORECASE)
_YEAR_RE = re.compile(r"^(\d{4})$")


def window_sort_key(date_or_window: str) -> tuple:
    """Pure sort key for a trajectory entry's free-text date_or_window
    field (see pipeline/schemas/trajectory.json -- deliberately unrestricted
    free text, since a regulator's own stated precision genuinely varies
    from an exact date down to a bare year, or a prose window like
    "mid-2026"). Recognizes, in order of decreasing precision:

      - an exact date: "2026-01-15"
      - a year-month: "2026-01"
      - a calendar quarter: "Q1 2026" or "2026 Q1" (case-insensitive)
      - a half-year: "H1 2026" or "2026 H1" (case-insensitive)
      - a bare year: "2026"

    Each recognized form is anchored to its window's START (e.g. "H2 2026"
    sorts as July 1 2026, "Q1 2026" as January 1 2026) so windows of
    different granularity still interleave into one reasonable
    chronological order rather than each granularity forming its own
    separate, un-comparable band.

    Anything matching none of the above (e.g. "mid-2026", "TBC", "early
    Q3") is the deliberate fallback case: it is NOT guessed at with a
    loose partial-year regex -- a wrong guess is worse than an honest
    "unparsed" for a page that exists specifically so readers can trust
    officially-stated timelines. Unparsed entries sort after every
    parseable entry (never interleaved among real dates on the strength of
    a guess), and alphabetically among themselves, so a build is
    deterministic rather than depending on source file/dict iteration
    order.

    Pure and total: never raises, safe to pass directly as sorted()'s
    key= for any string pipeline/schemas/trajectory.json accepts.
    """
    text = (date_or_window or "").strip()

    m = _EXACT_DATE_RE.match(text)
    if m:
        year, month, day = (int(g) for g in m.groups())
        return (0, year, month, day, "")

    m = _YEAR_MONTH_RE.match(text)
    if m:
        year, month = (int(g) for g in m.groups())
        return (0, year, month, 1, "")

    m = _QUARTER_RE.match(text)
    if m:
        quarter = int(m.group(1) or m.group(4))
        year = int(m.group(2) or m.group(3))
        month = (quarter - 1) * 3 + 1
        return (0, year, month, 1, "")

    m = _HALF_RE.match(text)
    if m:
        half = int(m.group(1) or m.group(4))
        year = int(m.group(2) or m.group(3))
        month = 1 if half == 1 else 7
        return (0, year, month, 1, "")

    m = _YEAR_RE.match(text)
    if m:
        year = int(m.group(1))
        return (0, year, 1, 1, "")

    return (1, 0, 0, 0, text.lower())


def build_glossary_jurisdiction_chips(glossary_terms: list, jurisdiction_names: dict) -> list:
    """Chip list for the Glossary page's jurisdiction filter (P7 plan):
    "All" plus one chip per REAL jurisdiction id that at least one term is
    actually tagged with, in config/site.json registry order. The
    sentinel "global" tag (see pipeline/schemas/glossary.json) never gets
    a chip of its own -- a term tagged "global" applies to every
    jurisdiction, so it is folded into every other chip's count instead
    (matching the exact show/hide logic site.js's glossary filter
    implements: a term is visible under jurisdiction X if it is tagged X
    OR "global"). Counts are real, computed here at build time from the
    actual term set -- never placeholders and never hand-maintained.
    """
    chips = [{"id": "all", "name": "All", "count": len(glossary_terms)}]
    for jid, name in jurisdiction_names.items():
        tagged_directly = any(jid in (term.get("jurisdictions") or []) for term in glossary_terms)
        if not tagged_directly:
            continue
        count = sum(
            1
            for term in glossary_terms
            if jid in (term.get("jurisdictions") or []) or "global" in (term.get("jurisdictions") or [])
        )
        chips.append({"id": jid, "name": name, "count": count})
    return chips


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
    # Every registry entry's id -> display name, in config/site.json order
    # -- SEEDED and PLANNED alike (unlike the per-jurisdiction content
    # loaders below, this is just registry metadata, cheap to keep for
    # every entry). Shared by aggregate_global_pages_data() (labelling
    # merged cards/documents/corrections) and the Glossary page's
    # jurisdiction-chip builder just above.
    jurisdiction_names = {j["id"]: j["name"] for j in site_config.get("jurisdictions", [])}

    glossary_terms = _load_json_glob(os.path.join(repo_root, "content", "shared", "glossary", "*.json"))
    glossary_terms = sorted((g for g in glossary_terms if g), key=lambda g: g["term"].lower())
    # Keyed by each term's own stable "id" (schema_version 2, see
    # pipeline/schemas/glossary.json) so related_terms crosslinks resolve
    # by id, not by a display-string match that would break on rename.
    glossary_terms_by_id = {g["id"]: g for g in glossary_terms if g.get("id")}

    corrections = _load_json(os.path.join(repo_root, "data", "corrections.json"), [])
    audit_latest = _load_json(os.path.join(repo_root, "data", "audit", "latest.json"))

    return {
        "site_config": site_config,
        "pillar_names": pillar_names,
        "pillar_index": pillar_index,
        "seal_labels": seal_labels,
        "seal_legend_copy": SEAL_LEGEND_COPY,
        "jurisdiction_names": jurisdiction_names,
        "glossary_terms": glossary_terms,
        "glossary_terms_by_id": glossary_terms_by_id,
        "glossary_jurisdiction_chips": build_glossary_jurisdiction_chips(glossary_terms, jurisdiction_names),
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

    trajectory = sorted(trajectory or [], key=lambda t: window_sort_key(t["date_or_window"]))
    for entry in trajectory:
        if entry["pillar"] not in pillar_names:
            raise SiteDataError(
                f"unmapped pillar id {entry['pillar']!r} in {trajectory_path} -- add it to "
                "pillars in config/site.json or fix the trajectory entry."
            )
        entry["pillar_name"] = pillar_names[entry["pillar"]]
        # Same fixed-positional-slot color channel the precise ribbon's
        # dated markers use (see build_timeline_events's pillar_color_slot
        # and the --pillar-color-N tokens in style.css) -- reused for the
        # Ahead rail's pills (_timeline.html) so a pillar reads as the same
        # color in both bands. Never -1 here: unlike a card/document, a
        # trajectory entry's "pillar" field is required by
        # pipeline/schemas/trajectory.json (minLength 1, no empty-array
        # case to sentinel around), and the unmapped-id check just above
        # already guarantees it is a real, configured pillar id.
        entry["pillar_color_slot"] = pillar_index[entry["pillar"]]

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

    # The earliest date this jurisdiction's watcher ever recorded seeing
    # ANY item (not just relevant ones) -- a real "live since" date for
    # the Method page's coverage table, derived from data/<id>/ledger.json
    # itself rather than a hand-typed date that could drift from the
    # truth. None if the ledger has no items yet (watcher configured but
    # never successfully run).
    first_seen_dates = sorted(i["first_seen"] for i in ledger_items if i.get("first_seen"))
    watcher_live_since = first_seen_dates[0][:10] if first_seen_dates else None

    orientation_split = split_orientation_body(orientation.get("body", ""))

    return {
        "config": config,
        "pillar_states": ordered_pillar_states,
        "cards": cards,
        "trajectory": trajectory,
        "documents": documents,
        "timeline_events": timeline_events,
        "orientation": orientation,
        "orientation_essay_items": orientation_split["essay_items"],
        "orientation_panel_notes": orientation_split["panel_notes"],
        "status_counts": status_counts,
        "ledger_item_count": len(ledger_items),
        "relevant_item_count": len(relevant_items),
        "watcher_live_since": watcher_live_since,
    }


def aggregate_global_pages_data(global_data: dict, jurisdiction_data_by_id: dict) -> dict:
    """Merges the per-jurisdiction data of every SEEDED jurisdiction (the
    `jurisdiction_data_by_id` mapping build_site() assembles by calling
    load_jurisdiction_data() once per registry entry with status.seeded ==
    true) into the combined view the three site-wide shared pages --
    Document Library, Glossary, Method & Audit -- render from. Glossary
    content needs no merging here: it already comes from load_global_data()
    as one shared pool, not a per-jurisdiction one. This replaces the P6
    load_site_data() scaffolding's single-hardcoded-jurisdiction shortcut
    (see PROGRESS.md's P6 entry) now that generate.py genuinely walks the
    registry instead of calling that wrapper for one hardcoded id.

    Each merged card/document carries its own jurisdiction_id and
    jurisdiction_name (looked up from global_data's registry) so a future
    template can label or filter by jurisdiction; today, with only "hk"
    seeded, this is inert plumbing rather than a visible change.
    """
    jurisdiction_names = global_data["jurisdiction_names"]

    all_cards = []
    all_documents = []
    ledger_item_count = 0
    relevant_item_count = 0
    status_counts: dict = {}
    for jurisdiction_id, jdata in jurisdiction_data_by_id.items():
        jurisdiction_name = jurisdiction_names.get(jurisdiction_id, jurisdiction_id)
        for card in jdata["cards"]:
            card = dict(card, jurisdiction_id=jurisdiction_id, jurisdiction_name=jurisdiction_name)
            all_cards.append(card)
        for doc in jdata["documents"]:
            doc = dict(doc, jurisdiction_id=jurisdiction_id, jurisdiction_name=jurisdiction_name)
            all_documents.append(doc)
        ledger_item_count += jdata["ledger_item_count"]
        relevant_item_count += jdata["relevant_item_count"]
        for status, count in jdata["status_counts"].items():
            status_counts[status] = status_counts.get(status, 0) + count

    all_cards.sort(key=lambda c: c["published_date"], reverse=True)
    all_documents.sort(key=lambda d: d.get("published_at") or "", reverse=True)

    # Join each correction to its card for a readable title/link on the
    # Method page -- falls back to a reader-appropriate placeholder (never
    # crashes, and never renders the raw 64-char card_id hash -- this page's
    # entire purpose is making corrections legible, CLAUDE.md rule 6) if no
    # matching card is found, e.g. a card that was later removed. Matches
    # against the full merged card set, not any single jurisdiction's,
    # since data/corrections.json is a global file (see load_global_data's
    # docstring) whose records can reference any jurisdiction's card.
    cards_by_id = {c["id"]: c for c in all_cards}
    corrections = sorted((global_data["corrections"] or []), key=lambda r: r["corrected_at"], reverse=True)
    for record in corrections:
        matching_card = cards_by_id.get(record["card_id"])
        if matching_card:
            record["card_title"] = matching_card["title"]
        else:
            record["card_title"] = f"Card {record['card_id'][:8]}… (no longer published)"
        # jurisdiction column (P7, schema_version bump on corrections.json
        # -- see pipeline/schemas/corrections.json): every record carries
        # its own "jurisdiction" id since data/corrections.json is a
        # single global file, not partitioned per jurisdiction. Falls back
        # to the raw id itself if it names a jurisdiction not (or no
        # longer) in the registry, same reader-appropriate-fallback
        # principle as card_title above -- never a raw KeyError, never a
        # silently blank cell.
        record_jurisdiction = record.get("jurisdiction", "unknown")
        record["jurisdiction_name"] = jurisdiction_names.get(record_jurisdiction, record_jurisdiction)

    return {
        "cards": all_cards,
        "documents": all_documents,
        "ledger_item_count": ledger_item_count,
        "relevant_item_count": relevant_item_count,
        "status_counts": status_counts,
        "corrections": corrections,
    }


def build_coverage_rows(site_config: dict, jurisdiction_data_by_id: dict) -> list:
    """Builds the Method page's per-jurisdiction coverage table -- one row
    per config/site.json registry entry, in registry order -- entirely
    from real data, never hand-written per-jurisdiction table rows in the
    template (see CLAUDE.md: "The Method page's coverage table is the
    public rendering of what is watched per jurisdiction, how, and since
    when").

    For a SEEDED jurisdiction, the regulator/mechanism detail comes from
    that jurisdiction's own load_jurisdiction_data() result: its real
    config/jurisdictions/{id}.json regulators list (a regulator with at
    least one feed becomes a "watched" row entry describing the feed kinds
    and count; a regulator configured with zero feeds becomes a named
    coverage gap instead of silently vanishing) and its watcher_live_since
    (the earliest date data/{id}/ledger.json has ever recorded seeing an
    item -- a real fact, not a hand-typed date). The registry entry's own
    coverage_notes free text is always appended to the gaps list too, for
    whatever a mechanical regulator/feed scan can't capture on its own.

    An UNSEEDED registry entry has no config file and no jurisdiction data
    yet (config: null in config/site.json) -- its row degrades to
    coverage_notes alone, with an empty regulators list, never a
    fabricated regulator/live-since for a watcher that doesn't exist.
    """
    rows = []
    for entry in site_config.get("jurisdictions", []):
        jid = entry["id"]
        status = entry.get("status", {})
        seeded = bool(status.get("seeded", False))
        jdata = jurisdiction_data_by_id.get(jid) if seeded else None

        regulators = []
        gaps = []
        live_since = None
        if jdata is not None:
            live_since = jdata.get("watcher_live_since")
            for regulator in (jdata.get("config") or {}).get("regulators", []):
                feeds = regulator.get("feeds") or []
                label = regulator.get("short_name") or regulator.get("name") or regulator.get("id", "")
                if feeds:
                    kinds = sorted({f["kind"] for f in feeds if f.get("kind")})
                    regulators.append(
                        {
                            "label": label,
                            "name": regulator.get("name", label),
                            "feed_count": len(feeds),
                            "kinds": kinds,
                        }
                    )
                else:
                    gaps.append(f"{label}: regulator configured, no feed wired yet")

        if entry.get("coverage_notes"):
            gaps.append(entry["coverage_notes"])

        rows.append(
            {
                "id": jid,
                "name": entry.get("name", jid),
                "seeded": seeded,
                "watcher_status": status.get("watcher", "planned"),
                "analyst_status": status.get("analyst_verifier", "planned"),
                "live_since": live_since,
                "regulators": regulators,
                "coverage_gaps": gaps,
            }
        )
    return rows
