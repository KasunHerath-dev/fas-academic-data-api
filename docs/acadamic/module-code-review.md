# Module-code review: timetable API vs WUSL documents

**Date:** 2026-11-17
**Compared:**
- Live timetable API (`GET /api/timetables/:level/sessions`), 2024/2025 Semester I, Levels 1–4
  (L1 "Revised 02" published 2026-10-05; L2–L4 "Revised" published 2026-09-10).
- `docs/wusl_module_tracker.md` (module catalogue, Prospectus 2020/2021).
- `docs/wusl_academic_flow.md` (academic rules).
- `docs/academic-structure-and-module-catalogue.md` §5 and §9 (earlier findings).
- How the app treats each code today (`client/src/utils/subjectPolicy.ts`, `timetableFilter.ts`).

Only **Semester I** is published in the API, so Semester II codes in the tracker can't be checked yet.

Status key: **Fix** = the best match is clear and safe to normalise. **Confirm** = needs an answer from
the faculty or the current prospectus before changing anything.

> **Update 2026-11-17: fixed.** B (`MIS 4142` → `CMIS 4142`) and A1/A2 (`+`/`ᵻ` → `†`, so `IMGT 3+34`
> and `IMGT 3ᵻ34` are one module `IMGT 3†34`) are implemented in
> `server/src/services/timetableTransform.ts` (`normalizeModuleCode`). Session IDs are still built from
> the raw code, so saved attendance stays attached with no data migration. The raw code is kept in
> `rawModuleCode`. Still open: A3 (session type for these cells), C2 (Business English), D and E.

---

## Summary

| # | Group | Codes | Status |
|---|---|---|---|
| A | `†` (dagger) misread as `+` or `ᵻ` | 10 codes | Fix the encoding; confirm titles |
| B | Prefix lost a letter | `MIS 4142` | Fix |
| C | Not real module codes | `Orientation`, `Business English`, `ELPC 1+10`, `ELPC 2+20` | Confirm credit status |
| D | Code in the timetable but not in the tracker | 11 codes | Confirm (probable curriculum revision) |
| E | Codes or terms the documents disagree on | 5 items | Confirm |

The ones that affect attendance numbers today: **A2** (one module split into two), **B** (a lecture hidden
from CMIS students) and **C2** (Business English counted in overall attendance).

---

## A. The `†` symbol read as `+` or `ᵻ`

The prospectus writes some codes with a dagger in the semester position: `CMIS 4†18` and `CMIS 4†26`
in the tracker. The rule from `wusl_academic_flow.md` is *XXXX X Y Z Q* = subject, level,
**semester**, module number, credits. So `†` in the semester digit most likely means the module **runs
in both semesters (year-long)**. That fits the data: these are labs, seminars and projects that appear
on many days.

The PDF text extraction turns `†` into `+` (or, once, `ᵻ`), and the parser then flags each one with
"Unusual character in subject code" and "Missing session type".

| API code | Level | Seen in timetable cell | Best match | Credits (last digit) | Confidence |
|---|---|---|---|---|---|
| `ELPC 1+10` | 1 | Mini Auditorium / MH, LR-01/02/03 | `ELPC 1†10`: English course, year-long, **0 credits** | 0 | High |
| `ELPC 2+20` | 2 | Mini Auditorium, LR 01/02/03 | `ELPC 2†20`: English course, year-long, **0 credits** | 0 | High |
| `ELTN 3+53` | 3 | Next to "Lab" | `ELTN 3†53`: ELTN year-long lab/project | 3 | Medium (title unknown) |
| `IMGT 3+34` | 3 | `(P)`, LR-05 | `IMGT 3†34`: same module as the next row | 4 | High |
| `IMGT 3ᵻ34` | 3 | `(P)` | `IMGT 3†34` | 4 | High |
| `ELTN 4+63` | 4 | "ELTN Lab" | `ELTN 4†63` | 3 | Medium (title unknown) |
| `ELTN 4+78` | 4 | "ELTN Lab" | `ELTN 4†78` | 8 | Medium: 8 credits matches a **Special research project** (`CMIS 4†18` is also 8) |
| `ELTN 4+86` | 4 | "ELTN Lab" | `ELTN 4†86` | 6 | Medium: 6 credits matches a **Joint Major research project** (`CMIS 4†26` is also 6) |
| `ELTN 4+92` | 4 | "Seminar Room ELTN" | `ELTN 4†92`: probably a seminar | 2 | Medium |
| `IMGT 4+06` | 4 | No room given | `IMGT 4†06`: 6 credits, probably an IMGT research project / training | 6 | Low: module number `0` is unusual |

**A1. Fix: one canonical form.** Normalise `+` and `ᵻ` in the semester position to `†` in the server
transform (`server/src/services/timetableTransform.ts`), keep the raw text in `rawCellText`, and drop the
"Unusual character" warning for this exact pattern. The pattern is `^[A-Z]{3,4} [1-4][+ᵻ†]\d{2}$`.

**A2. Attendance impact today.** `IMGT 3+34` and `IMGT 3ᵻ34` are two separate modules in the app. A
Level 3 IMGT student sees two cards for one module and their practical attendance is split between
them. Normalising (A1) merges them. Records already saved under either code need a one-time
**mapping** to `IMGT 3†34`, not a rewrite: per CLAUDE.md, history must not be silently remapped.

**A3. Session type.** None of these cells has `(L)`, `(T)` or `(P)`, so they get "Missing session type".
From the room text: "Lab" → `P`, "Seminar Room" → `L`. This should be confirmed before it is applied
automatically.

**To confirm:** the official titles for `ELTN 3†53`, `ELTN 4†63`, `ELTN 4†78`, `ELTN 4†86`,
`ELTN 4†92` and `IMGT 4†06`, and whether `†` really means "both semesters".

---

## B. A prefix that lost a letter

| API code | Level | Cell | Best match | Why | Confidence |
|---|---|---|---|---|---|
| `MIS 4142` | 4 | `MIS 4142 (L)`, LR-05, next to `STAT 4124` and `IMGT 4123` | **`CMIS 4142`: Image Processing (2 credits)** | `MIS` is not a FAS prefix. `CMIS 4142` exists in the tracker (L4 S1) **and** in this same timetable as a lecture. The leading `C` was dropped by OCR. | High |

**Attendance impact today.** The schedule filter selects sessions by subject prefix. `MIS` matches no
student, so this Image Processing lecture is **missing from every Level 4 CMIS student's day**.
Fix: map `MIS 4142` to `CMIS 4142` in the transform, and add `MIS` → `CMIS` to the prefix check
(warn, don't reject).

---

## C. Entries that are not real module codes

| API code | Level | What it is | How the app treats it now | Problem |
|---|---|---|---|---|
| `Orientation` | 1 | Orientation programme | Non-credit (in `NON_CREDIT_SUBJECT_PREFIXES`) | OK. Excluded from overall attendance. |
| `ELPC 1+10`, `ELPC 2+20` | 1, 2 | English Language Proficiency Course | Non-credit (prefix `ELPC`) | OK for attendance. Display code fixed by A1. |
| **`Business English`** | 3 | Level 3 English course (Mini Auditorium, LR 01/02/03, same rooms as ELPC) | **Counted as credit-bearing, 2 credits.** Its prefix `BUSINESS` is not in `NON_CREDIT_SUBJECT_PREFIXES`, so `getSubjectCredits` falls back to 2. | **C2: it is counted in overall attendance.** If it is auxiliary like ELPC (very likely: same rooms, no code, no credits), a Level 3 student's overall % is wrong. |

**C2 fix (after confirmation):** add `BUSINESS ENGLISH` to the non-credit list. It is a two-word name, so
the check has to match the full name, not only the first word. `timetableFilter.ts` already lists it as
"auxiliary".

**To confirm:** is Business English non-credit and compulsory for all Level 3 students? Is it the same
course as GAC, or separate?

---

## D. In the timetable but not in the tracker

These look valid, but the tracker (Prospectus 2020/2021) doesn't have them. They are probably
curriculum revisions. The app shows them by their code because it has no title for them.

| API code | Level | Closest code in tracker | Note |
|---|---|---|---|
| `CMIS 3124` | 3 | `CMIS 3122` Rapid Application Development (2 cr) | Same level, semester and module number; **credits differ (4 vs 2)**. Same module re-credited, or a new one? |
| `IMGT 4163` | 4 | `IMGT 4162` Financial Management (2 cr) | Same pattern: **3 vs 2 credits**. |
| `MATH 3114` | 3 | none (tracker has no Level 3 MATH in S1) | MATH module for the General split (COMB 1A/1C)? |
| `IMGT 3142` | 3 | none | |
| `IMGT 3152` | 3 | none | |
| `IMGT 3172` | 3 | none | Has practicals (`P`). |
| `ELTN 4122` | 4 | none | |
| `ELTN 4131` | 4 | none | 1-credit lab (`P`), probably the lab for `ELTN 4122`. |
| `IMGT 4184` | 4 | none | |
| `IMGT 4192` | 4 | none | |
| `STAT 4124` | 4 | none | |

**Attendance impact:** none on the percentages. Credits come from the last digit, and the app counts
attendance in hours. These only need **titles** and the **programme** they belong to (General, Joint
Major or Special) so setup can list the right modules.

Also, these tracker codes have **no sessions** in the Semester I timetable: `CMIS 3122`, `IMGT 4162`, and
the research projects `CMIS 4†18` and `CMIS 4†26`. Research projects are usually not timetabled, so that
is expected.

---

## E. Places where the documents disagree

| Item | What the documents say | Why it matters |
|---|---|---|
| `MMST` vs `MMOD` | The Joint Major table uses major `MMST`. The module catalogue only has `MMOD` and `STAT`. | Joint Major 1B and 2B students: which prefixes make up "MMST"? The app currently treats MMST as MATH + STAT + MMOD. |
| `ELPC` vs `ELPT` | The timetable and code list use ELPC (a course). The degree rules say "Pass ELPT I & II" (tests). | Keep them separate. ELPC is attendance; ELPT is a test result. |
| Credits per level | The flowchart says "Complete 10 credits minimum" per level, but the rules say "at least 30 credits per level". Sample pathways have 15 and 24-credit years. | Not an attendance issue, but `wusl_academic_flow.md` contradicts itself. Use **30–33 per year**, which matches the registration table. |
| Credit = hours | "1 credit = 15 lecture hours" vs "30–45 practical hours". | Fine for display. Do not use it to estimate total hours for attendance. Use the timetable. |
| Semester length | "2 semesters × 15 weeks" vs the API calendar's "Academic Session 08 Weeks" | The 15 weeks are split by a mid-semester vacation. Use the API calendar for dates. |

---

## Questions to take to the faculty or the prospectus

1. Does `†` in a module code mean "runs in both semesters"? What are the official titles of `ELTN 3†53`,
   `ELTN 4†63`, `ELTN 4†78`, `ELTN 4†86`, `ELTN 4†92` and `IMGT 4†06`?
2. Is Business English (Level 3) non-credit / auxiliary?
3. Were `CMIS 3122` → `CMIS 3124` and `IMGT 4162` → `IMGT 4163` re-credited? What are the titles of the
   other D-group codes, and which programmes are they for?
4. Which subject prefixes make up the `MMST` major?
5. Is there a 2024/2025 or newer prospectus that replaces the 2020/2021 tracker?

## Suggested order of fixes

1. **B** `MIS 4142` → `CMIS 4142`: a lecture is currently hidden; high confidence.
2. **A1/A2** normalise `+`/`ᵻ` → `†` and merge `IMGT 3†34`, with a mapping for saved records.
3. **C2** Business English as non-credit, once confirmed.
4. **D** add titles to the module catalogue as the faculty confirms them.

Note: line 1 of `wusl_module_tracker.md` asks for "once a level is selected, load that level's modules".
The setup wizard already does this from the timetable API. The tracker is useful for titles and credits
where the API has none.
