#!/usr/bin/env python3
"""Mérési eredmények összesítése (docker-bench + Trivy) Markdown táblákba.

Használat:
  python3 scripts/summarize.py evidence/<futás>                 # egy mérés
  python3 scripts/summarize.py evidence/<v1> evidence/<v2>      # összehasonlítás
"""
import json
import sys
from collections import Counter
from pathlib import Path

SECTIONS = {"1": "Host", "2": "Daemon", "3": "Daemon fájlok", "4": "Image / build",
            "5": "Runtime", "6": "Security ops", "7": "Swarm (N/A)"}
SEV = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]


def bench(run: Path) -> dict:
    d = json.loads((run / "docker-bench" / "docker-bench.log.json").read_text(encoding="utf-8"))
    results = {}
    for t in d["tests"]:
        for r in t["results"]:
            results[r["id"]] = r
    return {"score": d.get("score"), "checks": d.get("checks"), "results": results}


def trivy(run: Path) -> dict:
    out = {}
    for f in sorted((run / "trivy").glob("image_*.json")):
        text = f.read_text(encoding="utf-8")
        # A v1 mérésnél a Trivy naplósorai (stderr) a JSON elé kerültek: az első '{' sortól olvasunk.
        start = text.find("\n{") + 1 if not text.lstrip().startswith("{") else 0
        try:
            d = json.loads(text[start:])
        except json.JSONDecodeError:
            continue
        c = Counter()
        for res in d.get("Results", []) or []:
            for v in res.get("Vulnerabilities", []) or []:
                c[v.get("Severity", "UNKNOWN")] += 1
        meta = d.get("Metadata", {}).get("OS", {})
        out[d.get("ArtifactName", f.stem)] = (c, f"{meta.get('Family', '?')} {meta.get('Name', '')}".strip())
    return out


def section_counts(b: dict) -> dict:
    counts = {s: Counter() for s in SECTIONS}
    for rid, r in b["results"].items():
        s = rid.split(".")[0]
        if s in counts:
            counts[s][r["result"]] += 1
    return counts


def print_single(run: Path) -> None:
    b, t = bench(run), trivy(run)
    print(f"## {run.name}\n\ndocker-bench: {b['checks']} ellenőrzés, score = {b['score']}\n")
    print("| CIS fejezet | PASS | WARN | NOTE | INFO |\n|---|---|---|---|---|")
    for s, c in section_counts(b).items():
        print(f"| {s} {SECTIONS[s]} | {c['PASS']} | {c['WARN']} | {c['NOTE']} | {c['INFO']} |")
    print("\n### WARN tételek\n\n| ID | Leírás | Részletek |\n|---|---|---|")
    for rid, r in b["results"].items():
        if r["result"] == "WARN":
            det = (r.get("details") or "").replace("|", "/")[:110]
            print(f"| {rid} | {r['desc']} | {det} |")
    print("\n### Trivy – image sérülékenységek\n\n| Image | OS | " + " | ".join(SEV) + " |\n|---|---|" + "---|" * len(SEV))
    for img, (c, os_) in t.items():
        print(f"| {img} | {os_} | " + " | ".join(str(c[s]) for s in SEV) + " |")


def print_compare(r1: Path, r2: Path) -> None:
    b1, b2 = bench(r1), bench(r2)
    print(f"## Összehasonlítás: {r1.name} → {r2.name}\n")
    print(f"docker-bench score: {b1['score']} → {b2['score']}\n")
    print("| CIS fejezet | WARN v1 | WARN v2 | PASS v1 | PASS v2 |\n|---|---|---|---|---|")
    c1, c2 = section_counts(b1), section_counts(b2)
    for s in SECTIONS:
        print(f"| {s} {SECTIONS[s]} | {c1[s]['WARN']} | {c2[s]['WARN']} | {c1[s]['PASS']} | {c2[s]['PASS']} |")
    print("\n### Változott tételek\n\n| ID | Leírás | v1 | v2 |\n|---|---|---|---|")
    for rid, r in b1["results"].items():
        new = b2["results"].get(rid)
        if new and new["result"] != r["result"]:
            print(f"| {rid} | {r['desc']} | {r["result"]} | {new["result"]} |")
    t1, t2 = trivy(r1), trivy(r2)
    print("\n### Trivy – HIGH + CRITICAL\n\n| Mérés | Image | CRITICAL | HIGH | Összes |\n|---|---|---|---|---|")
    for label, t in (("v1", t1), ("v2", t2)):
        for img, (c, _) in t.items():
            print(f"| {label} | {img} | {c['CRITICAL']} | {c['HIGH']} | {sum(c.values())} |")


if __name__ == "__main__":
    runs = [Path(a) for a in sys.argv[1:]]
    if len(runs) == 1:
        print_single(runs[0])
    elif len(runs) == 2:
        print_compare(*runs)
    else:
        sys.exit(__doc__)
