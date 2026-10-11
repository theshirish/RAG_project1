"""
Golden Set Step 2: Full Golden Set Builder (200 questions: 130 happy / 45 hard / 25 edge).
Combines the hand-written items (items_happy.py, items_hard_edge.py) with the base data, then:
- checks every `notes` passage is verbatim in the CSV (aborts on failure)
- warns when numbers in `ideal_answer` are missing from `notes`
- adds source_slug / source_field / metadata (Central/State, state/UT, category, question type)

Usage:
`python scripts/golden_set/build_golden_full.py [csv] [happy_json] [out_jsonl]`
(defaults: data/test/IndianGovtScheme.csv scripts/golden_set/happy_sample.json
           data/golden_data_set_GOVT_Schemes_full.jsonl)
"""
import csv, json, re, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from items_happy import HAPPY
from items_hard_edge import HARD, EDGE

HERE = os.path.dirname(os.path.abspath(__file__))
CSV, HAPPY_JSON, OUT = (sys.argv[1:4] + [None] * 3)[:3]
CSV = CSV or "data/test/IndianGovtScheme.csv"
HAPPY_JSON = HAPPY_JSON or os.path.join(HERE, "happy_sample.json")
OUT = OUT or "data/golden_data_set_GOVT_Schemes_full.jsonl"
SRC_NAME = "data/test/" + os.path.basename(CSV)

STATES = ["Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
          "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
          "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
          "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
          "Andaman and Nicobar", "Chandigarh", "Lakshadweep", "Puducherry", "Ladakh"]
ALIASES = {
    "Dadra and Nagar Haveli and Daman and Diu": [r"Dadra (?:and|&) Nagar Haveli", r"Daman (?:and|&) Diu"],
    "Jammu and Kashmir": [r"Jammu (?:and|&) Kashmir", r"\bJ&K\b"],
    "Delhi": [r"\bDelhi\b"],
}
STATE_OVERRIDE = {"amas-haryana": "Haryana", "hss": "Not specified"}  # hss: CSV marks State, text describes a GoI scheme


def clean(s):
    return re.sub(r"\s+", " ", s.replace("﻿", " ")).strip()


rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
R = {}
for r in rows:
    r = {k: clean(v) for k, v in r.items() if k}
    R.setdefault(r["slug"], r)  # exact-duplicate rows share a slug; first wins


def infer_state(r):
    if r["level"] == "Central":
        return None
    if r["slug"] in STATE_OVERRIDE:
        return STATE_OVERRIDE[r["slug"]]
    text = r["scheme_name"] + " " + r["details"]
    hits = {s for s in STATES if re.search(r"\b" + re.escape(s) + r"\b", text)}
    hits |= {k for k, pats in ALIASES.items() if any(re.search(p, text) for p in pats)}
    if len(hits) > 1:
        hits.discard("Delhi")  # 'New Delhi' venue mentions
    return hits.pop() if len(hits) == 1 else None


sample = json.load(open(HAPPY_JSON))
items = []  # (level, qtype, q, a, [(slug, field, note)])
for idx, q, a, note in HAPPY:
    if isinstance(idx, str):
        _, slug, field = idx.split(":")
    else:
        slug, field = sample[idx]["slug"], sample[idx]["field"]
        note = note or sample[idx]["excerpt"]
    items.append(("happy_path", f"single_fact_{field}", q, a, [(slug, field, note)]))
items += [("hard_path", t, q, a, s) for t, q, a, s in HARD]
items += [("edge_path", t, q, a, s) for t, q, a, s in EDGE]

NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def nums(s):
    s = re.sub(r"(?<=\d)[,\s]+(?=\d{2,3}\b)", "", s)  # '25, 000' / '2,50,000' -> digits
    return {n.replace(",", "").rstrip(".").lstrip("0") or "0" for n in NUM.findall(s)}


errors, warnings, records = [], [], []
for i, (level, qtype, q, a, srcs) in enumerate(items, 1):
    rid = f"g-sc{i:03d}"
    for slug, field, note in srcs:
        if slug not in R:
            errors.append(f"{rid}: unknown slug {slug}")
        elif clean(note) not in R[slug][field]:
            errors.append(f"{rid}: note not verbatim in {slug}.{field}: {note[:80]}")
    if srcs:
        missing = nums(a) - nums(" ".join(n for *_, n in srcs))
        if missing:
            warnings.append(f"{rid}: answer numbers not in notes {sorted(missing)} :: {a[:90]}")
    slugs = list(dict.fromkeys(s for s, _, _ in srcs))
    if len(srcs) == 1:
        notes = clean(srcs[0][2])
    else:
        notes = " | ".join(f"[{R[s]['scheme_name']} - {f}] {clean(n)}" for s, f, n in srcs)
    lv = sorted({R[s]["level"] for s in slugs})
    records.append({
        "id": rid,
        "question": q,
        "ideal_answer": a,
        "notes": notes,
        "level": level,
        "source_slug": slugs,
        "source_field": list(dict.fromkeys(f for _, f, _ in srcs)),
        "metadata": {
            "scheme_level": ", ".join(lv) if lv else "N/A",
            "scheme_level_per_source": [R[s]["level"] for s in slugs],
            "scheme_name": [R[s]["scheme_name"] for s in slugs],
            "state_ut": [infer_state(R[s]) if R[s]["level"] == "State" else "Central" for s in slugs],
            "scheme_category": [R[s]["schemeCategory"] for s in slugs],
            "question_type": qtype,
            "answerable": bool(srcs),
            "source_file": SRC_NAME,
        },
    })

ids = [r["id"] for r in records]
assert len(ids) == len(set(ids))
unresolved = sorted({(s, R[s]["scheme_name"][:60]) for r in records for s, st in
                     zip(r["source_slug"], r["metadata"]["state_ut"]) if st is None})

print("errors:", len(errors)); print("\n".join(errors))
print("warnings:", len(warnings)); print("\n".join(warnings))
print("unresolved state:", unresolved)
print(collections.Counter(r["level"] for r in records), len(records))
print(collections.Counter(r["metadata"]["scheme_level"] for r in records))
if not errors:
    with open(OUT, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("wrote", OUT)
