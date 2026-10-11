"""
Golden Set Step 3: 30-row Sample Builder for the coding phase.
Writes a sample of the base data (rows copied byte-for-byte, same header/CRLF format) and a golden
set with a strict 1:1 mapping (one golden record per sample row), keeping the full set's
happy/hard/edge ratio (19/7/4). Only valid rows are used: unique slug and no empty required field.

Usage:
`python scripts/golden_set/build_golden_sample.py [full_csv] [full_golden] [out_csv] [out_golden]`
(defaults: data/test/IndianGovtScheme.csv data/golden_data_set_GOVT_Schemes_full.jsonl
           data/test/IndianGovtScheme_sample.csv data/golden_data_set_GOVT_Schemes_sample.jsonl)
"""
import csv, io, json, re, sys, collections

DEFAULTS = ["data/test/IndianGovtScheme.csv", "data/golden_data_set_GOVT_Schemes_full.jsonl",
            "data/test/IndianGovtScheme_sample.csv", "data/golden_data_set_GOVT_Schemes_sample.jsonl"]
FULL_CSV, FULL_GOLD, OUT_CSV, OUT_GOLD = (sys.argv[1:5] + DEFAULTS[len(sys.argv[1:5]):])[:4]
OUT_CSV_REL = "data/test/" + OUT_CSV.rsplit("/", 1)[-1]

# Golden items reused from the full set (all single-source, valid rows), in output order.
REUSE = {
    "happy_path": ["g-sc006", "g-sc024", "g-sc063", "g-sc120", "g-sc072", "g-sc060", "g-sc128", "g-sc021",
                   "g-sc026", "g-sc050", "g-sc123", "g-sc079", "g-sc125", "g-sc117", "g-sc062", "g-sc076",
                   "g-sc121", "g-sc070", "g-sc130"],
    "hard_path": ["g-sc137", "g-sc146", "g-sc162", "g-sc160", "g-sc175", "g-sc140", "g-sc147"],
    "edge_path": ["g-sc179", "g-sc199"],
}
B, E, D = "benefits", "eligibility", "details"
NEW_EDGE = [
    ("missing_info", "fbpmp",
     "What is the upper age limit for Puducherry's Free Bus Pass for Media Persons?",
     "The scheme data does not specify any age limit. Eligibility requires the applicant to be an Indian citizen, a native of Puducherry by birth or by continuous residence for not less than five years, to have served at least three years as a media person in Puducherry, and to be currently employed as a media person.",
     [(E, "The applicant should be a citizen of India. The applicant should be a native of the Union Territory of Puducherry by birth or by continuous residence for not less than five years. The applicant should have served for a minimum of three years as a media person in the Print/Electronic Media/News Agency in the Union Territory of Puducherry. The applicant should be employed as a media person in any Print/Electronic Media/News Agency during the application.")]),
    ("wrong_attribution", "ysrkn",
     "How much does Kerala's YSR Kapu Nestham scheme give to women?",
     "YSR Kapu Nestham is not a Kerala scheme; it is run by the Backward Classes Welfare (C) Department, Govt. of Andhra Pradesh. It gives a total of ₹75,000 over 5 years, i.e. ₹15,000 per annum.",
     [(D, 'The scheme "YSR Kapu Nestham" is a Social Empowerment Scheme by the Backward Classes Welfare(C) Department, Govt. of Andhra Pradesh.'),
      (B, "Financial Assistance of a total amount of ₹ 75,000/- over the period of 5 years i.e., ₹ 15,000/- per annum.")]),
]
NEW_STATE = {"fbpmp": "Puducherry", "ysrkn": "Andhra Pradesh"}
REQ = ["scheme_name", "slug", "details", "benefits", "eligibility", "application", "documents", "level",
       "schemeCategory", "tags"]


def clean(s):
    return re.sub(r"\s+", " ", s.replace("﻿", " ")).strip()


# --- read CSV keeping each record's raw bytes (one physical CRLF line per record, verified)
raw = open(FULL_CSV, "rb").read().decode("utf-8")
lines = raw.split("\r\n")
header, body = lines[0], [l for l in lines[1:] if l]
rows = [next(csv.DictReader(io.StringIO(header + "\r\n" + l))) for l in body]
assert len(rows) == 3400
slug_n = collections.Counter(r["slug"] for r in rows)
valid = {r["slug"] for r in rows if slug_n[r["slug"]] == 1 and all(r[k].strip() for k in REQ)}
idx = {r["slug"]: i for i, r in enumerate(rows)}
R = {r["slug"]: {k: clean(v) for k, v in r.items() if k} for r in rows}

full = {json.loads(l)["id"]: json.loads(l) for l in open(FULL_GOLD, encoding="utf-8")}
template_keys = list(next(iter(full.values())).keys())
template_meta = list(next(iter(full.values()))["metadata"].keys())

out = []
for level in ("happy_path", "hard_path", "edge_path"):
    for gid in REUSE[level]:
        r = json.loads(json.dumps(full[gid]))
        assert r["level"] == level and len(r["source_slug"]) == 1
        r["metadata"]["source_file"] = OUT_CSV_REL
        out.append(r)
    if level == "edge_path":
        for qtype, slug, q, a, segs in NEW_EDGE:
            for f, n in segs:
                assert clean(n) in R[slug][f], (slug, f)
            row = R[slug]
            notes = clean(segs[0][1]) if len(segs) == 1 else \
                " | ".join(f"[{row['scheme_name']} - {f}] {clean(n)}" for f, n in segs)
            out.append({
                "id": None, "question": q, "ideal_answer": a, "notes": notes, "level": level,
                "source_slug": [slug], "source_field": list(dict.fromkeys(f for f, _ in segs)),
                "metadata": {
                    "scheme_level": row["level"], "scheme_level_per_source": [row["level"]],
                    "scheme_name": [row["scheme_name"]],
                    "state_ut": [NEW_STATE[slug] if row["level"] == "State" else "Central"],
                    "scheme_category": [row["schemeCategory"]], "question_type": qtype,
                    "answerable": True, "source_file": OUT_CSV_REL,
                },
            })

for i, r in enumerate(out, 1):
    r["id"] = f"g-sc{i:03d}"

# --- checks
slugs = [r["source_slug"][0] for r in out]
assert len(out) == 30 and len(set(slugs)) == 30, "need 30 distinct source rows"
assert all(s in valid for s in slugs), [s for s in slugs if s not in valid]
assert all(list(r.keys()) == template_keys and list(r["metadata"].keys()) == template_meta for r in out)

# --- write CSV: header + selected raw lines, original order, original CRLF endings
sel = sorted(idx[s] for s in slugs)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(header + "\r\n" + "".join(body[i] + "\r\n" for i in sel))
with open(OUT_GOLD, "w", encoding="utf-8") as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

lv = collections.Counter(r["level"] for r in out)
print({k: f"{v} ({v / 30:.1%})" for k, v in lv.items()})
print("valid pool:", len(valid), "| CSV rows used:", [i + 1 for i in sel])
print("qtypes:", collections.Counter(r["metadata"]["question_type"] for r in out))
print("Central/State:", collections.Counter(R[s]["level"] for s in slugs))
print("categories:", len({R[s]["schemeCategory"].split(",")[0].strip() for s in slugs}))
print("states/UTs:", len({st for r in out for st in r["metadata"]["state_ut"]} - {"Central"}))
