"""Build the HKDA Brief data files from the source registry, module briefs and project profiles.

Usage: python3 site/build.py            (run from the repo root)
Outputs: site/app/data/sources.json, modules.json, projects.json
Only public, own-words fields are emitted. No source text is ever included.
"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = ROOT / "site" / "app" / "data"
OUT.mkdir(parents=True, exist_ok=True)

PUBLISHER = {"HKMA": "HKMA", "SFC": "SFC", "FSTB": "FSTB", "GovHK": "Government", "LegCo": "LegCo",
             "HKEX": "HKEX", "IRD": "IRD", "BIS": "BIS", "Other": "Other"}
TYPE_LABEL = {"press_release": "Press release", "circular": "Circular", "consultation": "Consultation",
              "speech": "Speech", "warning": "Warning", "SPM_module": "SPM module", "report": "Report",
              "other": "Other", "guideline": "Guideline", "policy_statement": "Policy statement",
              "conclusions": "Conclusions", "FAQ": "FAQ", "code": "Code", "webpage": "Web page",
              "page": "Web page", "discussion_paper": "Discussion paper", "register": "Register",
              "subsidiary_legislation": "Subsidiary legislation", "policy_address": "Policy Address",
              "enforcement": "Enforcement", "bill": "Bill", "ordinance": "Ordinance"}
STATUS_LABEL = {"in_force": "In force", "issued_future_effective": "Issued, not yet effective",
                "consultation": "Consultation", "conclusions": "Conclusions published", "bill": "Bill",
                "enacted_pending": "Enacted, not yet in force", "pilot": "Pilot",
                "announced_target": "Stated target", "exploratory": "Exploratory", "superseded": "Superseded",
                "historical": "Historical", "informational": "Information"}
TOPIC_LABEL = {"capital_prudential": "Capital and prudential", "vatp_regime": "Trading platforms (VATPs)",
               "policy_strategy": "Policy and strategy", "stablecoins": "Stablecoins",
               "aml_cft_sanctions": "AML/CFT and sanctions", "custody_key_management": "Custody and keys",
               "cbdc_ehkd_crossborder": "CBDC, e-HKD and cross-border",
               "tokenisation_securities_bonds": "Tokenised securities and bonds",
               "enforcement_fraud": "Enforcement and fraud", "va_intermediaries": "Intermediaries and dealing",
               "tokenised_deposits_ensemble": "Tokenised deposits and Ensemble",
               "law_making_status": "Law-making", "conduct_investor_protection": "Conduct and investor protection",
               "hkma_engagement": "Engaging the HKMA", "governance_risk": "Governance and risk",
               "va_funds_etfs": "VA funds and ETFs", "cyber_tech_security": "Cyber and technology",
               "bank_entity_structure": "Bank legal status", "tax_reporting": "Tax and reporting",
               "other_sectors": "Other sectors"}

STRIP = re.compile(r"^(Circular to (licensed|intermediaries)[^-–:]*?[-–:]\s*|Circular (on|to) |Letter to (HKAB|DTCA):\s*|"
                   r"New speech by [^:]+:\s*|Hong Kong Monetary Authority\s*-\s*)", re.I)


def publishers(issuer):
    parts = [p.strip() for p in (issuer or "Other").replace("&", "+").split("+") if p.strip()]
    return [PUBLISHER.get(p, "Other") for p in parts] or ["Other"]


def short_label(e):
    t = STRIP.sub("", e.get("title") or "").strip()
    t = re.sub(r"\s*\|.*$", "", t)            # BRDR "| Annex ..." tails
    t = re.sub(r"\s*\([^)]*\)\s*$", "", t) if len(t) > 60 else t
    words = t.split()
    if len(words) > 9:
        t = " ".join(words[:9]) + "…"
    year = (e.get("date") or "")[:4]
    return f"{'/'.join(publishers(e.get('issuer')))} · {t}" + (f" ({year})" if year else "")


def link(e):
    for k in ("deep_link_base", "source_url", "url"):
        u = (e.get(k) or "").strip()
        if u.startswith("http"):
            return u
    return ""


def build_sources():
    out = []
    reg = [json.loads(l) for l in open(DOCS / "research" / "source-registry.jsonl")]
    parents = {e.get("parent_id") for e in reg if e.get("parent_id")}
    for e in reg:
        out.append({
            "id": e["id"], "t": e.get("title", ""), "sl": short_label(e), "d": e.get("date") or "",
            "p": publishers(e.get("issuer")), "ty": TYPE_LABEL.get(e.get("doc_type"), "Other"),
            "st": STATUS_LABEL.get(e.get("status_as_of_2026_09_25"), "Information"),
            "imp": e.get("importance", "reference"), "br": e.get("bank_relevance") or "context",
            "ap": e.get("applies_to") or [], "tp": [TOPIC_LABEL.get(t, t) for t in (e.get("topics") or [])],
            "s": e.get("summary", ""), "w": e.get("why_it_matters_for_bank_HoDA", ""),
            "k": [[k.get("point", ""), k.get("locator", "")] for k in (e.get("key_points") or [])][:12],
            "rg": e.get("reading_guide", ""), "u": link(e),
            "hid": e["id"] in parents,   # catalogue page whose document has its own entry
        })
    out.sort(key=lambda x: x["d"], reverse=True)
    return out


PARTS = {"A": "Orientation", "B": "Your bank as a regulated entity", "C": "Activities",
         "D": "Risk and control", "E": "Horizon and reference"}
START = {"A1", "B1", "B2", "C3", "C4", "D3", "E1"}


def build_modules():
    mods = []
    for f in sorted((DOCS / "modules").glob("*.md")):
        md = f.read_text()
        m = re.match(r"#\s+([A-E]\d)\s+(.+)", md)
        code, title = m.group(1), m.group(2).strip()
        body = md.split("\n", 1)[1].strip()
        words = len(re.findall(r"\w+", re.sub(r"\[S:[^\]]*\]", "", body)))
        mods.append({"code": code, "title": title, "part": code[0], "partTitle": PARTS[code[0]],
                     "start": code in START, "minutes": max(5, round(words / 200)), "md": body})
    return mods


def build_projects():
    d = DOCS / "projects"
    out = []
    if d.exists():
        for f in sorted(d.glob("*.md")):
            md = f.read_text()
            m = re.match(r"#\s+(.+)", md)
            out.append({"slug": f.stem, "title": m.group(1).strip() if m else f.stem,
                        "md": md.split("\n", 1)[1].strip()})
    return out


if __name__ == "__main__":
    src = build_sources()
    mods = build_modules()
    projs = build_projects()
    ids = {s["id"] for s in src}
    missing = sorted({i for m in mods + projs for i in re.findall(r"\[S:([0-9a-f]{12})", m["md"]) if i not in ids})
    if missing:
        raise SystemExit(f"Unknown citation ids: {missing[:10]}")
    for name, data in (("sources", src), ("modules", mods), ("projects", projs)):
        (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    print(f"sources={len(src)} modules={len(mods)} projects={len(projs)}")
