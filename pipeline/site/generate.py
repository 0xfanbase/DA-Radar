"""Static site generator -- renders content/*.json and data/*.json into
static HTML under an output directory (_site/ by default), uploaded to
GitHub Pages via the Actions-based deployment (actions/upload-pages-artifact
+ actions/deploy-pages). This output directory is never committed to git.

No JS framework, no npm build toolchain: Jinja2 templates + plain CSS/JS,
consistent with the rest of this pipeline's plain-Python, fully-testable
approach. Regenerated in full on every run (never incrementally patched),
same principle as every other derived file in this project.

Registry-model output layout (P7 -- see CLAUDE.md "Jurisdiction
portability" and PROGRESS.md's P6/P7 entries):

  _site/index.html              global landing page, all-jurisdiction grid
  _site/<jid>/index.html        per-jurisdiction Current State page
  _site/<jid>/timeline.html     per-jurisdiction Timeline page
  _site/documents.html          shared, aggregated across every SEEDED
  _site/glossary.html             jurisdiction (today just "hk")
  _site/method.html
  _site/<legacy path>.html      pre-P7 redirect stubs (see REDIRECT_STUBS)

One <jid>/index.html + <jid>/timeline.html pair is written for EVERY entry
in config/site.json's jurisdictions[] registry, seeded or not -- an
unseeded jurisdiction gets a real, valid "coming soon" page (coming_soon.html),
never a 404 or an empty file.
"""
from __future__ import annotations

import argparse
import os
import shutil

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pipeline.site.data import (
    aggregate_global_pages_data,
    build_coverage_rows,
    load_global_data,
    load_jurisdiction_data,
)
from pipeline.watcher.clock import utc_now_iso

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Shared pages: one copy each, at the site root, built from data aggregated
# across every SEEDED jurisdiction (see aggregate_global_pages_data()).
# Unlike the per-jurisdiction pages, these don't branch on seeded status --
# an unseeded jurisdiction simply contributes nothing to the aggregate yet,
# same as it contributing zero cards/documents today.
SHARED_PAGES = [
    ("documents.html", "documents.html", "documents"),
    ("glossary.html", "glossary.html", "glossary"),
    ("method.html", "method.html", "method"),
]

# Legacy paths from the pre-P7, single-jurisdiction site layout, which had
# no jurisdiction segment in any URL because "hk" was the only jurisdiction
# that could ever exist in that layout. P7 moved that same content to
# jurisdiction-scoped paths under content/hk/... (config/site.json's
# founding, and -- as of P7 -- still only seeded, jurisdiction).
# These stubs keep the old URLs resolvable instead of 404ing for anyone who
# bookmarked or linked them; deliberately hardcoded to "hk" rather than
# derived, because that is a fact about this deployment's history (there
# was exactly one jurisdiction before P7), not a jurisdiction-agnostic
# pipeline rule -- a jurisdiction onboarded after P7 never had pre-P7 URLs
# to redirect from, so it needs no entry here. See CLAUDE.md's own logged,
# reasoned deviations for the same pattern of an explicit, narrow exception
# to portability that doesn't generalize.
REDIRECT_STUBS = [
    ("state-board.html", "hk/index.html"),
    ("trajectory.html", "hk/timeline.html"),
    ("timeline.html", "hk/timeline.html"),
]


def _render(env: Environment, template_name: str, output_path: str, **context) -> str:
    template = env.get_template(template_name)
    html = template.render(**context)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return output_path


def _write_redirect_stub(output_path: str, target_url: str) -> str:
    """A minimal, real HTML file -- never a 404 -- for a pre-P7 URL that
    moved. Plain <meta http-equiv="refresh"> for browsers that honor it,
    PLUS a visible "this page has moved" link for crawlers, no-JS clients,
    and anything that doesn't honor meta refresh -- no JS redirect, per
    this project's plain-HTML-first ethos (CLAUDE.md)."""
    html = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        f'<meta http-equiv="refresh" content="0; url={target_url}">\n'
        "<title>This page has moved</title>\n"
        "</head>\n"
        "<body>\n"
        f'<p>This page has moved. <a href="{target_url}">Continue to the new page</a>.</p>\n'
        "</body>\n"
        "</html>\n"
    )
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return output_path


def build_site(repo_root: str, output_dir: str) -> list:
    """Renders the full multi-jurisdiction site into output_dir. Returns
    the list of output file paths written, for callers that want to
    inspect or test them.

    All content/data loading happens BEFORE anything is written -- if any
    jurisdiction's data fails to load (SiteDataError, see pipeline/site/
    data.py), this function raises before touching output_dir at all, so a
    failed build never leaves partial or stale output on disk.
    """
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    global_data = load_global_data(repo_root)
    site_name = global_data["site_config"].get("site_name", "")
    registry = global_data["site_config"].get("jurisdictions", [])

    # Computed once per build, passed to every template so the footer (see
    # base.html) can show a real "page generated" timestamp on every page --
    # distinct from a jurisdiction's own content_last_updated (when the
    # displayed facts were last touched by an analyst run): this one
    # answers "when was this HTML itself produced," so a reader can tell
    # a same-day rebuild with nothing new to say apart from a stale rebuild
    # that hasn't run in a while.
    build_generated_at = utc_now_iso()

    # The header's row-1 nav (see pipeline/site/templates/base.html) always
    # shows Current State/Timeline links, even on pages with no jurisdiction
    # context of their own (the global landing page, Document Library,
    # Glossary, Method & Audit) -- those two links need SOME jurisdiction to
    # point at. Falls back to the first SEEDED entry in registry order
    # (today: "hk", the founding jurisdiction) rather than the bare first
    # registry entry, so the default never lands a reader on a coming-soon
    # page from a plain nav click; falls back further to the first entry at
    # all only if the registry somehow has no seeded jurisdiction yet.
    default_jurisdiction_id = next(
        (e["id"] for e in registry if e.get("status", {}).get("seeded", False)),
        registry[0]["id"] if registry else None,
    )

    # --- Load phase: every seeded jurisdiction's data, plus the aggregate
    # the shared pages need. Nothing is written to disk yet.
    jurisdiction_data_by_id = {}
    for entry in registry:
        if entry.get("status", {}).get("seeded", False):
            jurisdiction_data_by_id[entry["id"]] = load_jurisdiction_data(repo_root, entry["id"], global_data)
    shared_data = aggregate_global_pages_data(global_data, jurisdiction_data_by_id)
    # Method page's coverage table -- one row per registry entry, real
    # regulator/feed/live-since data for seeded jurisdictions, coverage_notes
    # alone for planned ones. See build_coverage_rows()'s own docstring.
    coverage_rows = build_coverage_rows(global_data["site_config"], jurisdiction_data_by_id)

    # --- Write phase: loading above succeeded, safe to start writing.
    os.makedirs(output_dir, exist_ok=True)
    static_out = os.path.join(output_dir, "static")
    if os.path.exists(static_out):
        shutil.rmtree(static_out)
    shutil.copytree(STATIC_DIR, static_out)

    written = []

    # Global landing page: a thin, all-jurisdiction grid. No per-jurisdiction
    # content lives here -- that's what <jid>/index.html is for.
    written.append(
        _render(
            env,
            "landing.html",
            os.path.join(output_dir, "index.html"),
            active_page="landing",
            asset_prefix="",
            build_generated_at=build_generated_at,
            site_name=site_name,
            jurisdictions=registry,
            default_jurisdiction_id=default_jurisdiction_id,
        )
    )

    # One Current State + Timeline page per registry entry, live content for
    # seeded jurisdictions, a real "coming soon" placeholder for the rest.
    for entry in registry:
        jid = entry["id"]
        jurisdiction_name = entry["name"]
        seeded = entry.get("status", {}).get("seeded", False)
        if seeded:
            jdata = jurisdiction_data_by_id[jid]
            written.append(
                _render(
                    env,
                    "current_state.html",
                    os.path.join(output_dir, jid, "index.html"),
                    active_page="current_state",
                    asset_prefix="../",
                    build_generated_at=build_generated_at,
                    site_name=site_name,
                    jurisdictions=registry,
                    default_jurisdiction_id=default_jurisdiction_id,
                    jurisdiction_id=jid,
                    jurisdiction_name=jurisdiction_name,
                    seal_labels=global_data["seal_labels"],
                    seal_legend_copy=global_data["seal_legend_copy"],
                    **jdata,
                )
            )
            # Merged 3-band Timeline page (precise ribbon, Ahead rail,
            # "Ahead, by pillar" board) -- see pipeline/site/templates/
            # timeline.html and _timeline.html for the band layout itself;
            # this call is just the routing/data-loading, unchanged since
            # the single-band version.
            written.append(
                _render(
                    env,
                    "timeline.html",
                    os.path.join(output_dir, jid, "timeline.html"),
                    active_page="timeline",
                    asset_prefix="../",
                    build_generated_at=build_generated_at,
                    site_name=site_name,
                    jurisdictions=registry,
                    default_jurisdiction_id=default_jurisdiction_id,
                    jurisdiction_id=jid,
                    jurisdiction_name=jurisdiction_name,
                    **jdata,
                )
            )
        else:
            for output_name, active_page in (("index.html", "current_state"), ("timeline.html", "timeline")):
                written.append(
                    _render(
                        env,
                        "coming_soon.html",
                        os.path.join(output_dir, jid, output_name),
                        active_page=active_page,
                        asset_prefix="../",
                        build_generated_at=build_generated_at,
                        site_name=site_name,
                        jurisdictions=registry,
                        default_jurisdiction_id=default_jurisdiction_id,
                        jurisdiction_id=jid,
                        jurisdiction_name=jurisdiction_name,
                        coverage_notes=entry.get("coverage_notes", ""),
                    )
                )

    # Shared pages, aggregated across every SEEDED jurisdiction.
    for template_name, output_name, active_page in SHARED_PAGES:
        written.append(
            _render(
                env,
                template_name,
                os.path.join(output_dir, output_name),
                active_page=active_page,
                asset_prefix="",
                build_generated_at=build_generated_at,
                site_name=site_name,
                jurisdictions=registry,
                default_jurisdiction_id=default_jurisdiction_id,
                audit_latest=global_data["audit_latest"],
                glossary_terms=global_data["glossary_terms"],
                glossary_terms_by_id=global_data["glossary_terms_by_id"],
                glossary_jurisdiction_chips=global_data["glossary_jurisdiction_chips"],
                jurisdiction_names=global_data["jurisdiction_names"],
                coverage_rows=coverage_rows,
                **shared_data,
            )
        )

    # Legacy redirect stubs -- never a 404 for a pre-P7 bookmarked URL.
    for old_path, new_path in REDIRECT_STUBS:
        written.append(_write_redirect_stub(os.path.join(output_dir, old_path), new_path))

    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build the Global Digital Asset Radar static site.")
    parser.add_argument("--repo-root", default=".")
    # Deliberately NOT "docs/" -- that directory already holds
    # docs/analyst-runbook.md (Phase 2's operational runbook, unrelated to
    # this generated site). Also never committed to git: deploy.yml uploads
    # this directory straight to GitHub Pages via the official Actions
    # deployment (actions/upload-pages-artifact + actions/deploy-pages),
    # so its name only matters within a single workflow run.
    parser.add_argument("--output-dir", default="_site")
    args = parser.parse_args(argv)

    written = build_site(args.repo_root, args.output_dir)
    print(f"site: wrote {len(written)} page(s) to {args.output_dir}")
    for path in written:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
