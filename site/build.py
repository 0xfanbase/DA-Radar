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


PARTS = {"F": "Business and opportunities", "A": "Orientation", "B": "Your bank as a regulated entity", "C": "Activities",
         "D": "Risk and control", "E": "Horizon and reference"}
START = {"A1", "B1", "B2", "C3", "C4", "D3", "E1"}


def build_modules():
    mods = []
    for f in sorted((DOCS / "modules").glob("*.md"), key=lambda f: (f.stem[0], int(re.sub(r"\D", "", f.stem) or 0), f.stem)):
        md = f.read_text()
        m = re.match(r"#\s+([A-F]\d[a-z]?)\s+(.+)", md)
        code, title = m.group(1), m.group(2).strip()
        body = md.split("\n", 1)[1].strip()
        body = re.sub(r"(## Related modules\s*\n)(.*?)(?=\n## |\Z)",
                      lambda m: m.group(1) + re.sub(r"\b([A-F]\d[a-z]?)\b(?![^\[]*\])", r"[\1](#m-\1)", m.group(2)), body, flags=re.S)
        words = len(re.findall(r"\w+", re.sub(r"\[S:[^\]]*\]", "", body)))
        mods.append({"code": code, "title": title, "part": code[0], "partTitle": PARTS[code[0]],
                     "start": code in START, "minutes": max(5, round(words / 200)), "md": body})
    return mods


def short_by(v):
    """'Hong Kong Monetary Authority (HKMA) with the Bank of Thailand (BoT), ...' -> 'HKMA and partners'."""
    acr = []
    for t in re.findall(r"\b(?:[A-Z]{2,}[A-Za-z]*|CMU OmniClear)\b", v):
        if t not in acr and t not in ("HKSAR",):
            acr.append(t)
    if not acr:
        return re.split(r"[;,(]", v)[0].strip()[:40]
    return acr[0] if len(acr) == 1 else (" + ".join(acr) if len(acr) == 2 else acr[0] + " and partners")


def build_projects():
    d = DOCS / "projects"
    out = []
    if d.exists():
        for f in sorted(d.glob("*.md")):
            md = f.read_text()
            m = re.match(r"#\s+(.+)", md)
            body = md.split("\n", 1)[1].strip()
            body = re.sub(r"^(\| Covered in \|)(.*?)\|\s*$",
                          lambda m: m.group(1) + " " + re.sub(r"\b([A-F]\d[a-z]?)\b", r"[\1](#m-\1)", m.group(2).strip()) + " |",
                          body, flags=re.M)
            glance = {r[0]: r[1] for r in table_rows(section(md, "At a glance")) if len(r) >= 2}
            plain = lambda v: re.sub(r"\s*\[S:[^\]]*\]", "", v or "").strip()
            status = plain(next((v for k, v in glance.items() if k.startswith("Status")), ""))
            out.append({"slug": f.stem, "title": m.group(1).strip() if m else f.stem, "md": body,
                        "oneLine": re.sub(r"\s*\[S:[^\]]*\][;,]?", "", body.split("\n\n", 1)[0]).strip(),
                        "runBy": short_by(plain(glance.get("Run by", ""))),
                        "status": re.split(r"\s*[(;:—]", status)[0].strip(),
                        "coveredIn": re.sub(r"\[([A-F]\d[a-z]?)\]\(#m-[A-F]\d[a-z]?\)", r"\1", plain(glance.get("Covered in", "")))})
    return out


def section(md, name):
    m = re.search(r"^## " + re.escape(name) + r"[^\n]*\n(.*?)(?=^## |\Z)", md, re.S | re.M)
    return m.group(1) if m else ""


def table_rows(text):
    rows = [l for l in text.splitlines() if l.startswith("|")]
    out = []
    for l in rows[2:]:
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", l.strip()[1:-1])]
        out.append(cells)
    return out


def bullets_by_label(text):
    """Yield (label, bullet_markdown) for '**Label**' groups followed by '- ' bullets."""
    label = None
    for line in text.splitlines():
        m = re.match(r"^\*\*(.+?)\*\*\s*$", line.strip())
        if m:
            label = m.group(1)
        elif line.startswith("- ") and label:
            yield label, line[2:].strip()


MONTHS = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}


def sort_key(d):
    m = re.match(r"(?:(\d{1,2}) )?(?:([A-Z][a-z]{2})\w* )?(\d{4})", d)
    if not m:
        return "0000"
    day, mon, yr = m.groups()
    return f"{yr}-{MONTHS.get(mon, 0):02d}-{int(day or 0):02d}"


AUD = {"To the CEO": "CEO", "To the CCO": "CCO", "To business heads": "Business", "To Risk / CRO": "Risk"}
CAT = {"Obligations": "Obligations", "Controls & monitoring": "Controls and monitoring",
       "Notify / consult HKMA or SFC": "Notify or consult", "Counterparty due diligence": "Counterparty due diligence"}


PAUD = {"CEO": "CEO", "CCO": "CCO", "business heads": "Business", "Risk": "Risk", "Risk / CRO": "Risk", "CRO": "Risk"}


def build_extras(mods, projs=()):
    obligations, talking = [], []
    for m in mods:
        if m["code"] == "E3":
            continue
        for lab, b in bullets_by_label(section(m["md"], "What your bank must do")):
            obligations.append({"code": m["code"], "cat": CAT.get(lab, lab), "md": re.sub(r"^\[[ xX]?\]\s*", "", b)})
        for lab, b in bullets_by_label(section(m["md"], "Talking points")):
            talking.append({"code": m["code"], "aud": AUD.get(lab, lab), "md": b})
    for p in projs:
        for line in section(p["md"], "Talking points").splitlines():
            t = re.match(r"^- \*\*To (?:the )?(.+?):\*\*\s*(.+)$", line.strip())
            if t and t.group(1) in PAUD:
                talking.append({"code": "p-" + p["slug"], "aud": PAUD[t.group(1)], "md": t.group(2)})
    e3 = next(m["md"] for m in mods if m["code"] == "E3")
    timeline = [{"d": r[0], "k": sort_key(r[0]), "ev": r[1], "by": r[2], "src": r[3]}
                for r in table_rows(section(e3, "Part B")) if len(r) >= 4]
    glossary, group = [], ""
    for line in section(e3, "Part A").splitlines():
        g = re.match(r"^\*\*(.+?)\*\*\s*$", line.strip())
        if g:
            group = g.group(1)
        elif line.startswith("|") and not re.match(r"^\|\s*(Term|---)", line):
            c = [x.strip() for x in line.strip()[1:-1].split("|")]
            if len(c) >= 3:
                glossary.append({"term": c[0], "def": c[1], "src": c[2], "g": group})
    e1 = next(m["md"] for m in mods if m["code"] == "E1")
    coming = [{"what": r[0], "by": r[1], "when": r[2], "st": r[3], "who": r[4], "src": r[5]}
              for r in table_rows(section(e1, "Status board")) if len(r) >= 6 and not re.match(r"Superseded", r[3])]
    log = (DOCS / "CHANGELOG.md").read_text() if (DOCS / "CHANGELOG.md").exists() else ""
    changes = [{"d": m.group(1), "md": m.group(2).strip()} for m in re.finditer(r"^## (.+?)\n(.*?)(?=^## |\Z)", log, re.S | re.M)]
    return {"changes": changes[:6], "obligations": obligations, "talking": talking, "timeline": timeline, "glossary": glossary, "coming": coming}


IND_CLASS = {"international_official": ("intl", "International official"), "foreign_regulator": ("foreign", "Foreign regulator"),
             "listed_filing": ("filing", "Company filing"), "consultancy": ("industry", "Industry estimate"),
             "bank_research": ("industry", "Industry estimate"), "association": ("industry", "Industry estimate"),
             "data_provider": ("industry", "Industry estimate")}


def build_industry():
    """Non-official sources for Part F (docs/research/industry-registry.jsonl). Never mixed into official facts."""
    p = DOCS / "research" / "industry-registry.jsonl"
    out = []
    if not p.exists():
        return out
    for line in open(p):
        if not line.strip():
            continue
        e = json.loads(line)
        cls, label = IND_CLASS.get(e.get("publisher_type"), ("industry", "Industry estimate"))
        figs = [[f"{g.get('metric','')}: {g.get('value','')} {g.get('unit','')}".strip() +
                 f" ({', '.join(x for x in [g.get('as_of',''), g.get('scope',''), g.get('estimate_type','')] if x)})",
                 g.get("locator", "")] for g in (e.get("figures") or [])]
        rules = [[r.get("point", ""), r.get("locator", "")] for r in (e.get("rules") or [])]
        year = (e.get("date") or "")[:4]
        out.append({"id": e["id"], "t": e.get("title", ""), "sl": f"{e.get('publisher','')} · {e.get('title','')[:60]} ({year})",
                    "d": e.get("date") or "", "p": [e.get("publisher", "Other")], "ty": label, "st": label,
                    "imp": "reference", "br": "context", "ap": [], "tp": e.get("topics") or [],
                    "s": e.get("summary", ""), "w": "", "k": (figs + rules)[:14],
                    "rg": " ".join(x for x in [e.get("methodology_note", ""), e.get("caveats", "")] if x),
                    "u": e.get("url", ""), "hid": False, "cls": cls, "geo": e.get("geography", ""),
                    "sponsor": e.get("sponsor", ""), "conflict": bool(e.get("conflict"))})
    return out


LINE_STATUS = re.compile(r"^(In force|Pilot|Consultation|Conclusions published|Bill before LegCo|Stated target|Exploratory|Issued|Proposed)", re.I)


def build_business():
    d = DOCS / "business"
    lines, cases, compare = [], [], None
    plain = lambda v: re.sub(r"\s*\[[SI]:[^\]]*\]", "", v or "").strip()
    for f in sorted((d / "lines").glob("*.md")) if (d / "lines").exists() else []:
        md = f.read_text()
        title = re.match(r"#\s+(.+)", md).group(1).strip()
        body = md.split("\n", 1)[1].strip()
        g = {r[0]: r[1] for r in table_rows(section(md, "At a glance")) if len(r) >= 2}
        st = plain(g.get("Status as of 25 Sep 2026", ""))
        m = LINE_STATUS.match(st)
        rel = plain(g.get("Related modules", ""))
        body = re.sub(r"^(\| Related modules \|)(.*?)\|\s*$",
                      lambda m2: m2.group(1) + " " + re.sub(r"\b([A-F]\d[a-z]?)\b", r"[\1](#m-\1)", m2.group(2).strip()) + " |",
                      body, flags=re.M)
        case_titles = {c.stem: re.match(r"#\s+(.+)", c.read_text()).group(1).strip() for c in (d / "cases").glob("*.md")} if (d / "cases").exists() else {}
        body = re.sub(r"^(\| Related cases \|)(.*?)\|\s*$",
                      lambda m2: m2.group(1) + " " + ", ".join(f"[{case_titles[x.strip()]}](#case-{x.strip()})" if x.strip() in case_titles else x.strip()
                                                            for x in m2.group(2).split(",")) + " |", body, flags=re.M)
        lines.append({"slug": f.stem, "title": title, "md": body,
                      "oneLine": re.sub(r"\s*\[[SI]:[^\]]*\][;,]?", "", body.split("\n\n", 1)[0]).replace("(concept)", "").strip(),
                      "role": plain(g.get("Bank role", "")), "segments": plain(g.get("Client segments", "")),
                      "chain": [c.strip() for c in plain(g.get("Value chain", "")).split(",") if c.strip()],
                      "status": m.group(1) if m else (st.split(".")[0][:30] if st else ""),
                      "related": rel, "cases": plain(g.get("Related cases", "")),
                      "nS": len(re.findall(r"(?:\[|;\s*)S:[0-9a-f]{12}", body)),
                      "nI": len(re.findall(r"(?:\[|;\s*)I:[0-9a-f]{12}", body))})
    for f in sorted((d / "cases").glob("*.md"), key=lambda f: int(re.match(r"\d+", f.stem).group(0)) if re.match(r"\d+", f.stem) else 99) if (d / "cases").exists() else []:
        md = f.read_text()
        m = re.match(r"#\s+(.+)", md)
        body = md.split("\n", 1)[1].strip()
        situation = re.sub(r"\s*\[[SI]:[^\]]*\][;,]?", "", section(md, "The situation")).strip().split("\n\n")[0]
        words = len(re.findall(r"\w+", re.sub(r"\[[SI]:[^\]]*\]", "", body)))
        cases.append({"slug": f.stem, "title": m.group(1).strip() if m else f.stem, "md": body,
                      "teaser": situation[:280], "minutes": max(5, round(words / 200))})
    if (d / "compare-sg-uae.md").exists():
        md = (d / "compare-sg-uae.md").read_text()
        m = re.match(r"#\s+(.+)", md)
        compare = {"title": m.group(1).strip() if m else "Hong Kong, Singapore and the UAE", "md": md.split("\n", 1)[1].strip()}
    return {"lines": lines, "cases": cases, "compare": compare}


if __name__ == "__main__":
    src = build_sources()
    ind = build_industry()
    mods = build_modules()
    projs = build_projects()
    biz = build_business()
    ids = {s["id"] for s in src}
    iids = {s["id"] for s in ind}
    texts = [m["md"] for m in mods + projs + biz["lines"] + biz["cases"]] + ([biz["compare"]["md"]] if biz["compare"] else [])
    missing = sorted({i for t in texts for i in re.findall(r"(?:\[|;\s*)S:([0-9a-f]{12})", t) if i not in ids})
    imissing = sorted({i for t in texts for i in re.findall(r"(?:\[|;\s*)I:([0-9a-f]{12})", t) if i not in iids})
    if missing or imissing:
        raise SystemExit(f"Unknown citation ids: official {missing[:10]} industry {imissing[:10]}")
    src = src + ind
    extras = build_extras(mods, projs)
    for name, data in (("sources", src), ("modules", mods), ("projects", projs), ("extras", extras), ("business", biz)):
        (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    print(f"sources={len(src)} (industry {len(ind)}) modules={len(mods)} projects={len(projs)} lines={len(biz['lines'])} cases={len(biz['cases'])} " +
          " ".join(f"{k}={len(v)}" for k, v in extras.items()))
