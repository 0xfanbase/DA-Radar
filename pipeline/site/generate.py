"""Static site generator -- renders content/*.json and data/*.json into
static HTML under an output directory (docs/ by default, matching a
common GitHub Pages "deploy from branch, /docs folder" source setting).

No JS framework, no npm build toolchain: Jinja2 templates + plain CSS/JS,
consistent with the rest of this pipeline's plain-Python, fully-testable
approach. Regenerated in full on every run (never incrementally patched),
same principle as every other derived file in this project.
"""
from __future__ import annotations

import argparse
import os
import shutil

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pipeline.site.data import load_site_data

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

PAGES = [
    ("start_here.html", "index.html", "start_here"),
    ("state_board.html", "state-board.html", "state_board"),
    ("trajectory.html", "trajectory.html", "trajectory"),
    ("timeline.html", "timeline.html", "timeline"),
    ("documents.html", "documents.html", "documents"),
    ("glossary.html", "glossary.html", "glossary"),
    ("method.html", "method.html", "method"),
]


def build_site(repo_root: str, output_dir: str) -> list:
    """Renders every page into output_dir. Returns the list of output
    file paths written, for callers that want to inspect or test them."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    site_data = load_site_data(repo_root)

    os.makedirs(output_dir, exist_ok=True)
    static_out = os.path.join(output_dir, "static")
    if os.path.exists(static_out):
        shutil.rmtree(static_out)
    shutil.copytree(STATIC_DIR, static_out)

    written = []
    for template_name, output_name, active_page in PAGES:
        template = env.get_template(template_name)
        html = template.render(active_page=active_page, asset_prefix="", **site_data)
        output_path = os.path.join(output_dir, output_name)
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(html)
        written.append(output_path)

    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build the HK Digital Asset Radar static site.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", default="docs")
    args = parser.parse_args(argv)

    written = build_site(args.repo_root, args.output_dir)
    print(f"site: wrote {len(written)} page(s) to {args.output_dir}")
    for path in written:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
