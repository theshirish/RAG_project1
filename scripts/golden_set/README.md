# Golden Sets for the Government Schemes RAG

This folder builds the **golden sets**: hand-checked questions with known-correct answers. We use them to measure how well the RAG system answers questions about Indian government schemes.

There are two golden sets, each tied to a base-data file:

| Purpose | Base data (what the RAG indexes) | Golden set (what we test with) | Size |
|---|---|---|---|
| **Final check after every successful commit** | `data/test/IndianGovtScheme.csv` | `data/golden_data_set_GOVT_Schemes_full.jsonl` | 3,400 schemes / 200 questions |
| **Coding phase** (fast runs while developing) | `data/test/IndianGovtScheme_sample.csv` | `data/golden_data_set_GOVT_Schemes_sample.jsonl` | 30 schemes / 30 questions, one question per scheme |

> **Always pair the files as shown.** The sample golden set only works against the sample CSV, because every answer comes from one of its 30 rows. Running it against the full CSV is fine. Running the *full* golden set against the *sample* CSV will fail most questions, because those schemes aren't in it.

---

## 1. Quick start

Run all commands from the **project root**. They use only Python's standard library (built and tested on Python 3.14) and need no extra installs.

```bash
# Rebuild the 200-question full golden set
python scripts/golden_set/build_golden_full.py

# Rebuild the 30-row sample CSV + its golden set (reads the full golden set, so run this second)
python scripts/golden_set/build_golden_sample.py
```

Both scripts are **deterministic**: running them again produces byte-identical files. If you haven't edited anything and `git diff` shows changes after a rebuild, something has drifted (see [Section 9](#9-regenerating-and-editing)).

---

## 2. Files in this folder

| File | Role |
|---|---|
| `sample_schemes.py` | **Step 1.** Picks 129 schemes from the CSV with a fixed random seed and writes `happy_sample.json`. For each scheme it records one field (benefits / eligibility / documents / application) and one short passage from that field. *Normally you never re-run this* (see Section 9). |
| `happy_sample.json` | Output of Step 1, kept in the repo. The happy-path questions refer to its entries by index (`0`–`128`). |
| `items_happy.py` | The 130 **happy-path** questions and ideal answers, written by hand. |
| `items_hard_edge.py` | The 45 **hard** and 25 **edge** questions and ideal answers, written by hand. Each lists its source scheme(s), field(s) and the exact source passage. |
| `build_golden_full.py` | **Step 2.** Combines the questions with the CSV, validates every record and writes the full golden set. |
| `build_golden_sample.py` | **Step 3.** Picks 30 records from the full golden set, adds 2 new edge records, writes the 30-row sample CSV and the matching golden set. |

---

## 3. The base data (`IndianGovtScheme.csv`)

The CSV has one government scheme per row: 3,400 rows, 541 Central and 2,859 State.

```
scheme_name,slug,details,benefits,eligibility,application,documents,level,schemeCategory,,tags
```

> `data/test/` also contains `IndianGOVTSchemes_Dataset.csv`, which has a similar name. It is a **different file** that the golden sets do not use. The base data is `IndianGovtScheme.csv` (it used to be called `updated_data.csv`).

- `slug` is the scheme's short ID (e.g. `pmay-g`). The golden sets use it to point at the source row.
- `level` is `Central` or `State`.
- `schemeCategory` is a comma-separated list. The first entry is the *primary* category, and there are 15 primary categories in total.
- The **11th column has an empty header and is always empty.** It's part of the original format, so keep it.
- The file has **no BOM**, uses **CRLF** line endings, and has **one physical line per record** (no field contains a newline). The sample CSV keeps all of these exactly.
- Some text contains invisible characters (`U+FEFF`) and irregular spacing. When matching text, the scripts remove these characters and collapse runs of whitespace (`clean()` in each script).

### 3.1 Valid vs. invalid rows

A row is **valid** when:
1. its `slug` appears only once in the file, **and**
2. none of `scheme_name, slug, details, benefits, eligibility, application, documents, level, schemeCategory, tags` is empty, **and**
3. `level` is `Central` or `State`.

That gives **3,355 valid rows and 45 invalid rows**:

| Reason | Rows |
|---|---|
| Empty `tags` | 29 |
| Empty `documents` | 10 |
| Duplicate `slug` (`eogu` ×3, `vcy` ×2; these are exact copies of each other) | 5 |
| Empty `application` | 2 |

(The reasons add up to 46 because one row has two problems.)

**Where the rule applies:**
- **Sample set:** uses only valid rows, enforced by an assertion in `build_golden_sample.py`.
- **Full set:** applies only the duplicate-slug rule. A duplicate slug can't identify a single correct row, so those rows are never used as sources. Three full-set source rows have an empty field the question doesn't use, so their answers are still correct:
  - `nari-adalat`: empty `documents`
  - `agroforestry`: empty `tags`
  - `dog`: empty `tags`

---

## 4. Golden record format

Each file is **JSONL**: one complete JSON object per line, UTF-8, with `₹` and other characters written literally (not escaped).

```json
{
  "id": "g-sc162",
  "question": "can i get a loan to build my pucca house under pmay gramin?? how much n at what interest",
  "ideal_answer": "Yes. Under PMAY-Gramin a willing beneficiary can take institutional finance (a loan) of up to ₹70,000 at a 3% lower interest rate to build a permanent house.",
  "notes": "A willing beneficiary can avail of institutional finance (loan) of up to ₹ 70,000 at 3% lower interest rate, to build a permanent house.",
  "level": "hard_path",
  "source_slug": ["pmay-g"],
  "source_field": ["benefits"],
  "metadata": {
    "scheme_level": "Central",
    "scheme_level_per_source": ["Central"],
    "scheme_name": ["Pradhan Mantri Awaas Yojana - Gramin"],
    "state_ut": ["Central"],
    "scheme_category": ["Housing & Shelter"],
    "question_type": "colloquial",
    "answerable": true,
    "source_file": "data/test/IndianGovtScheme.csv"
  }
}
```

### 4.1 Field reference

The first five fields match the format of the original sample `data/golden_set.jsonl`. The rest were added later and appear after them, so code that reads only the first five keeps working.

| Field | Type | Meaning |
|---|---|---|
| `id` | string | `g-sc001` … `g-sc200` (full) or `g-sc001` … `g-sc030` (sample). The prefix stands for "golden – schemes". **The two files number their IDs separately**: `g-sc005` in the sample is *not* the same question as `g-sc005` in the full set. |
| `question` | string | What a user would type. Some questions are deliberately casual, Hinglish or misspelled. |
| `ideal_answer` | string | The correct answer, using only facts from the CSV. For unanswerable questions it says the data doesn't cover the topic. |
| `notes` | string | The **exact source passage(s)** from the CSV that support the answer (see 4.2). Empty (`""`) when nothing in the data answers the question. |
| `level` | string | `happy_path` / `hard_path` / `edge_path` (see Section 5). |
| `source_slug` | list[str] | Slug(s) of the CSV row(s) holding the answer. `[]` for unanswerable questions. Use it for **retrieval metrics** (Recall@k, MRR). |
| `source_field` | list[str] | CSV column(s) the passage came from: `benefits`, `eligibility`, `documents`, `application` or `details`. |
| `metadata.scheme_level` | string | `Central`, `State`, `Central, State` (sources of both kinds) or `N/A` (no source). |
| `metadata.scheme_level_per_source` | list[str] | Level of each slug, in the same order as `source_slug`. |
| `metadata.scheme_name` | list[str] | Scheme name of each slug. |
| `metadata.state_ut` | list[str] | State/UT of each slug, or `"Central"` for Central schemes (see 4.3). |
| `metadata.scheme_category` | list[str] | The full `schemeCategory` text of each slug. |
| `metadata.question_type` | string | Finer label within the level (see Section 5). |
| `metadata.answerable` | bool | `false` when the data contains no answer (made-up scheme, off-topic question). |
| `metadata.source_file` | string | The base-data CSV this record was built against. |

### 4.2 `notes` format
- **One source passage:** the passage itself, with whitespace cleaned.
- **Two or more passages:** each one gets a label, and they're joined with ` | `:
  `[Scheme name - field] passage | [Scheme name - field] passage`

Every passage is guaranteed to appear **word for word** in the CSV after `clean()`. The build stops if any passage doesn't.

### 4.3 How `state_ut` is filled
The CSV has no state column, so `build_golden_full.py` works out the state from `scheme_name` + `details`:
- It matches the text against a list of states and UTs, plus aliases for *J&K* and *Dadra & Nagar Haveli and Daman & Diu*.
- If several states match, it ignores *Delhi*, because "New Delhi" is often just an event venue.
- A small `STATE_OVERRIDE` table handles cases the matching misses:
  - `amas-haryana` → Haryana
  - `hss` → `Not specified` (see Section 8)

Every inferred value in the current files was checked by hand. The two files cover 31 different states/UTs.

---

## 5. What the questions test

### 5.1 Levels and question types (full set: 200)

| Level | Count | `question_type` | n | What it tests |
|---|---|---|---|---|
| **happy_path** | 130 (65%) | `single_fact_benefits` | 51 | One plain fact from one scheme, e.g. an amount, age limit, document list or where to apply. |
| | | `single_fact_eligibility` | 45 | |
| | | `single_fact_documents` | 20 | |
| | | `single_fact_application` | 14 | |
| **hard_path** | 45 (22.5%) | `multi_field` | 12 | Combining two fields of one scheme (e.g. eligibility **and** benefit). |
| | | `eligibility_reasoning` | 10 | Applying a rule to the user's situation ("I'm 42, can I apply?"). |
| | | `comparison` | 8 | Comparing two schemes, or two groups within one scheme. |
| | | `colloquial` | 8 | Casual or Hinglish wording that retrieval must still map to the right scheme. |
| | | `partial_misconception` | 7 | The question contains a wrong assumption the answer must correct. |
| **edge_path** | 25 (12.5%) | `false_premise` | 8 | States a wrong number as fact. The system must correct it, not agree. |
| | | `non_existent_scheme` | 5 | Asks about a made-up scheme. The system must say it isn't in the data. |
| | | `out_of_scope` | 4 | Not about Indian schemes at all (US Social Security, cricket, coding, tax slabs). |
| | | `ambiguous` | 4 | The name matches several schemes. The system should list the versions or ask which one. |
| | | `misspelling` | 4 | A badly misspelled scheme name that should still be found. |

**How the 5 made-up schemes were checked:** each topic (electric car, gold loan, pet insurance, crypto, air ticket) was searched across all CSV text. There were **zero matches**, so the correct answer really is "not in the data".

### 5.2 Sample set (30) — same mix, strict 1:1

| Level | Count | Types |
|---|---|---|
| happy_path | 19 (63.3%) | benefits 8, eligibility 5, documents 3, application 3 |
| hard_path | 7 (23.3%) | multi_field 2, eligibility_reasoning 2, colloquial 1, partial_misconception 1, comparison 1 (two groups within one scheme) |
| edge_path | 4 (13.3%) | false_premise 1, misspelling 1, **missing_info 1**, **wrong_attribution 1** |

19/7/4 is the closest whole-number split to the full set's 65/22.5/12.5.

**Why the sample's edge types differ.** The sample requires *one golden record for each CSV row*. Four full-set edge types can't meet that rule:
- `non_existent_scheme` and `out_of_scope` have **no** source row.
- `ambiguous` and two-scheme `comparison` need **two or more** rows.

In their place, the sample adds two edge types that each use exactly one row. These two appear **only** in the sample set:
- `missing_info`: asks for a detail the scheme doesn't have (an age limit for Puducherry's Free Bus Pass for Media Persons). The right answer is "not specified", which tests that the system doesn't make one up.
- `wrong_attribution`: gives the wrong state for a real scheme (calls Andhra Pradesh's YSR Kapu Nestham a Kerala scheme). The right answer corrects the state.

The other 28 sample records are copied word for word from the full set, with new IDs.

---

## 6. How the full set was built

1. **Sampling (`sample_schemes.py`, seed `20261011`).**
   - Excludes rows with a duplicate slug.
   - Gives each primary category a share of the 129 picks in proportion to its size, with a minimum of 2.
   - Assigns about 40 picks to Central schemes. That's about 32% of picks against 16% of the data, so Central schemes are tested enough.
   - Shuffles the target fields to 50 benefits / 45 eligibility / 20 documents / 15 application.
   - For each scheme, picks one short passage from the target field. Benefits and eligibility passages must contain a number or ₹. Application passages must mention a portal, website or office.
   - Public Safety yielded no usable passage for one pick, so only 129 schemes came out. The 130th happy question (Tripura mob-violence compensation, `tlmvvcs`) was added by hand.
2. **Writing questions (`items_happy.py`).**
   - One question and answer was written from each passage.
   - Where the automatic passage was vague or cut off mid-sentence, a better passage from the same field was used instead (the 4th value in each tuple).
3. **Hard and edge questions (`items_hard_edge.py`).**
   - These come from a second, separate random pick of schemes not already used, chosen because they had both a ₹ benefit and an age/income rule.
   - Ambiguous questions use schemes whose names really do collide: IGNWPS Central vs J&K, construction-worker Maternity Benefit in Assam/Chandigarh/HP, Gujarat Goat Unit (10+1) for General/SC/ST, and construction-worker Disability Pension in Delhi vs Karnataka.
4. **Build and check (`build_golden_full.py`).** See Section 7.

The result: **202 different schemes**, spread across the whole file (rows 33 to 3,389), all 15 categories, 65 Central and 137 State.

## 7. Checks the build runs

`build_golden_full.py`:
- **Error, which stops the build:** a `notes` passage isn't word for word in its source field, or a slug doesn't exist.
- **Warning only:** a number in `ideal_answer` doesn't appear in `notes`. The current build prints 11 warnings, all checked and harmless:
  - 9 are the user's age, quoted from the question ("a 42-year-old is not eligible").
  - 1 is the "10+1" in a scheme name.
  - 1 is the number checker merging "₹1,50,000, 51%" into a single number.
- Prints any State scheme whose state couldn't be worked out. The list should be empty.
- Asserts that all IDs are unique.

`build_golden_sample.py`:
- **Exactly 30 different source rows**, all of them valid (Section 3.1).
- **Strict 1:1 mapping:** every golden record has exactly one `source_slug`.
- **Same structure as the full set:** the same keys in the same order, at the top level and in `metadata`.
- **CSV rows copied as raw bytes**, keeping the original header, CRLF endings and original row order.
- Checks the two new edge records' passages for exact wording, just like the full set.

---

## 8. Known limitations and things to watch

- **Only part of the data is covered.** The full set tests 202 of 3,355 valid schemes (about 6%). The other ~3,150 schemes are not tested directly.
- **`scheme_level` copies the CSV's label, even where it looks wrong.** "Hathkargha Samvardhan Sahayata" (`hss`) is marked `State` but describes a Government of India scheme. Its `state_ut` is `Not specified`.
- **The original `data/golden_set.jsonl` is not valid JSONL.** Each record spans several lines, with commas between records. Write your loader for standard JSONL (`json.loads` per line), which is the format of both new files.
- **Central schemes are deliberately over-represented** (about 32% of records vs 16% of the data). If you report accuracy for "all schemes", say that it is not weighted by data size.
- **Answers are exactly what the CSV says, not checked against the real world.** If the CSV is out of date (e.g. an amount has since changed), the golden answer is out of date too.
- **The eval code is still a stub.** `src/eval/golden.py` and `scripts/run_eval.py` contain only docstrings so far. The golden files were designed so a loader that reads only `id, question, ideal_answer, notes, level` works unchanged.

---

## 9. Regenerating and editing

| You want to… | Do this |
|---|---|
| Fix the wording of a question/answer | Edit `items_happy.py` or `items_hard_edge.py` → run step 2 → run step 3. |
| Use a different source passage for a happy question | Set the 4th tuple value in `items_happy.py` to the new passage (copied exactly from the CSV) → step 2 → step 3. |
| Add a hard/edge question | Add a tuple to `HARD` or `EDGE` in `items_hard_edge.py` → step 2 → step 3. **Note:** IDs follow file order, so every record after the insertion point gets a new ID. Append to the end of `EDGE` if you need existing IDs to stay the same. |
| Change which 30 rows/questions are in the sample | Edit `REUSE` (full-set IDs) or `NEW_EDGE` in `build_golden_sample.py` → step 3. Keep 19/7/4 and use one row per question. |
| Change the sample size | Edit `REUSE`/`NEW_EDGE` and the `30` checks at the end of `build_golden_sample.py`. |

**Do not re-run `sample_schemes.py`** unless you plan to rewrite all happy questions. `items_happy.py` refers to `happy_sample.json` by position, so a new pick (from a changed CSV or a different seed) would put every question on the wrong scheme. The build would then stop with "note not verbatim" errors. That stop is intended: it prevents silent damage to the golden set.

**If `IndianGovtScheme.csv` changes:** run step 2 first. Any golden record whose source text changed or was removed will stop the build with an error naming the record. Fix those records in the item files, then run step 3.

---

## 10. Using the golden sets in evaluation

These suggestions don't depend on how the evaluation code is written:

- **Answer quality** (all records): compare the RAG answer with `ideal_answer`, using an LLM judge or semantic similarity. `notes` gives the judge the ground-truth passage.
- **Retrieval quality** (`metadata.answerable == true`): check whether the retrieved chunks come from the scheme(s) in `source_slug`. This gives Recall@k / MRR. For `ambiguous` and two-scheme `comparison` questions, look for *all* listed slugs.
- **Refusing when there's no answer** (`answerable == false` and `missing_info`): the answer should say the data doesn't cover it, and must not invent a figure.
- **Correcting the user** (`false_premise`, `partial_misconception`, `wrong_attribution`): the answer must reject the user's claim, not agree with it.
- **Breakdowns:** report scores by `level` and `question_type`, and by `metadata.scheme_level` (Central vs State) to find weak spots.

Recommended loop: use the **sample** pair (30 questions) while coding, for fast feedback, and run the **full** pair (200 questions) after each successful commit.
