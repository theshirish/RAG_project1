"""
Golden Set Step 1: Stratified Scheme Sampler.
Picks 129 schemes (stratified by category and Central/State, fixed seed) from the base data and
extracts a short verbatim excerpt per scheme. Hand-written questions in items_happy.py refer to
these entries by index, so re-running this must reproduce happy_sample.json exactly.

Usage:
`python scripts/golden_set/sample_schemes.py [csv] [out_json]`
(defaults: data/test/IndianGovtScheme.csv scripts/golden_set/happy_sample.json)
"""
import csv, json, os, random, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = sys.argv[1] if len(sys.argv) > 1 else "data/test/IndianGovtScheme.csv"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "happy_sample.json")
random.seed(20261011)

STATES = ["Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
          "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
          "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
          "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
          "Andaman and Nicobar", "Chandigarh", "Dadra and Nagar Haveli", "Daman and Diu", "Delhi",
          "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"]


def clean(s):
    return re.sub(r"\s+", " ", s.replace("﻿", " ")).strip()


def infer_state(row):
    if row["level"] == "Central":
        return None
    text = row["scheme_name"] + " " + row["details"]
    hits = {s for s in STATES if re.search(r"\b" + re.escape(s) + r"\b", text)}
    hits.discard("Delhi") if len(hits) > 1 else None
    return hits.pop() if len(hits) == 1 else None


def sentences(s):
    return [p.strip() for p in re.split(r"(?<=[.;])\s+(?=[A-Z₹(\d])", s) if p.strip()]


def excerpt(text, field):
    sents = sentences(text)
    if field in ("benefits", "eligibility"):
        good = [s for s in sents if re.search(r"₹|\d", s) and 40 <= len(s) <= 420]
    elif field == "documents":
        return text if 30 <= len(text) <= 450 else None
    else:  # application
        good = [s for s in sents if re.search(r"portal|website|https?://|visit|office|apply online", s, re.I)
                and 40 <= len(s) <= 420]
    return random.choice(good) if good else None


rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
slug_count = collections.Counter(r["slug"] for r in rows)
for r in rows:
    for k in ("scheme_name", "details", "benefits", "eligibility", "application", "documents", "tags", "schemeCategory"):
        r[k] = clean(r[k])
rows = [r for r in rows if slug_count[r["slug"]] == 1]  # avoid ambiguous ground truth

FIELDS = ["benefits"] * 50 + ["eligibility"] * 45 + ["documents"] * 20 + ["application"] * 15
random.shuffle(FIELDS)
N = len(FIELDS)  # 130 happy
N_CENTRAL = 40

by_cat = collections.defaultdict(list)
for r in rows:
    by_cat[r["schemeCategory"].split(",")[0].strip()].append(r)

# proportional allocation with a floor of 2 per category
alloc = {c: max(2, round(N * len(v) / len(rows))) for c, v in by_cat.items()}
while sum(alloc.values()) > N:
    alloc[max(alloc, key=alloc.get)] -= 1
while sum(alloc.values()) < N:
    alloc[max(alloc, key=lambda c: len(by_cat[c]) / alloc[c])] += 1

picked, used = [], set()
central_quota = N_CENTRAL
fi = 0
for cat, n in sorted(alloc.items()):
    pool = by_cat[cat][:]
    random.shuffle(pool)
    # give Central schemes a share in each category proportional to the global quota
    want_central = round(n * N_CENTRAL / N)
    pool.sort(key=lambda r: 0 if (r["level"] == "Central" and want_central > 0) else 1)
    taken = 0
    for r in pool:
        if taken == n:
            break
        if r["slug"] in used:
            continue
        if r["level"] == "Central":
            if want_central <= 0:
                continue
        field = FIELDS[fi % N]
        ex = excerpt(r[field], field)
        if not ex:
            continue
        if r["level"] == "Central":
            want_central -= 1
        used.add(r["slug"])
        picked.append({"slug": r["slug"], "name": r["scheme_name"], "scheme_level": r["level"],
                       "category": r["schemeCategory"], "state": infer_state(r),
                       "field": field, "excerpt": ex})
        fi += 1
        taken += 1

json.dump(picked, open(OUT, "w"), ensure_ascii=False, indent=1)
print(len(picked), collections.Counter(p["scheme_level"] for p in picked),
      collections.Counter(p["field"] for p in picked), file=sys.stderr)
