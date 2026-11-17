# WUSL Faculty of Applied Sciences --- Consolidated Academic Structure & Module Catalogue

**Purpose:** Consolidated reference built from the two supplied files:
`wusl_academic_flow.md` and `wusl_module_tracker.md`. It combines the
academic pathway, subject combinations, degree-programme structure, and
the complete module list provided by the tracker.

> **Important source limitation:** These files are not an official live
> module-registration feed. The academic-flow document says it is based
> on the WUSL Prospectus 2020/2021 and was last updated in December
> 2024. The module tracker contains possible transcription errors in two
> Level 4 research-project codes and does not explicitly map every
> module to every programme, specialization, combination, or timetable
> session. Items that cannot be confirmed from these files are clearly
> marked rather than guessed.

## 1. Executive summary

-   Faculty: Faculty of Applied Sciences, Wayamba University of Sri
    Lanka (WUSL).
-   Instruction medium stated in the academic-flow file: English.
-   Academic structure: Levels 1--4, each with Semester I and Semester
    II.
-   Degree pathways described: B.Sc. General (3 years), B.Sc. Joint
    Major (4 years), and B.Sc. Special (4 years).
-   Level 1 and Level 2 students select one of three subject
    combinations.
-   At Level 3, the General pathway may split MATH and STAT into
    separate subject areas; Joint Major students select two majors;
    Special students select a specialization.
-   The supplied module tracker lists modules by level and semester. It
    should be treated as a **candidate catalogue**, not proof that every
    listed module is offered to every student.
-   AttendTrack should use the current FAS timetable API and the
    student's saved academic setup to determine the actual sessions
    shown to the student. Do not hardcode this whole catalogue as a
    substitute for current timetable data.

## 2. Academic structure

### 2.1 Levels and semesters

  -----------------------------------------------------------------------
  Level                   Academic year           Semesters
  ----------------------- ----------------------- -----------------------
  Level 1                 Year 1                  Semester I and Semester
                                                  II

  Level 2                 Year 2                  Semester I and Semester
                                                  II

  Level 3                 Year 3                  Semester I and Semester
                                                  II

  Level 4                 Year 4, for four-year   Semester I and Semester
                          pathways                II
  -----------------------------------------------------------------------

The academic-flow source describes each semester as 15 teaching weeks,
followed by two weeks of study leave and a four-week examination period.
Actual calendars and dates should be taken from current faculty
announcements.

### 2.2 Subject areas and codes

  Code   Subject area described in the supplied files
  ------ ----------------------------------------------
  CMIS   Computing & Information Systems
  ELTN   Electronics
  IMGT   Industrial Management
  MATH   Mathematics
  MMOD   Mathematical Modelling
  STAT   Statistics
  INDT   Industrial Training
  ELPC   English Language Proficiency Course

The academic-flow document uses **MMST** in its Joint Major table, while
the subject-code list and module tracker use **MMOD** and **STAT**. The
supplied files do not establish whether `MMST` is an official alias, a
programme label, or a typo. Do not automatically rewrite `MMST` to
`MMOD` without confirmation from the faculty or current timetable data.

### 2.3 Level 1--2 subject combinations

The academic-flow source states that students select one combination and
study the three subject areas in it.

  Combination   Subject area 1   Subject area 2   Subject area 3
  ------------- ---------------- ---------------- ----------------
  COMB 1        MATH & STAT      CMIS             ELTN
  COMB 2        MATH & STAT      ELTN             IMGT
  COMB 3        MATH & STAT      IMGT             CMIS

The module catalogue below lists modules by subject code. It does
**not** mean every module in each listed subject is necessarily
registered by every student in that combination. In particular,
practicals, electives, programme-specific modules, and modules not
offered in a given semester must be confirmed from the current timetable
and registration rules.

### 2.4 General degree split at Level 3

The supplied academic-flow file gives this example for students from
COMB 1:

-   **COMB 1A:** MATH + CMIS + ELTN
-   **COMB 1B:** STAT + CMIS + ELTN
-   **COMB 1C:** MATH + STAT + CMIS

This is an example from the source, not a complete mapping for all
possible Level 3 pathways. Do not infer undocumented splits for COMB 2
or COMB 3.

## 3. Degree pathways

### 3.1 B.Sc. General

The source describes this as a three-year pathway covering Levels 1--3.

  -----------------------------------------------------------------------
  Requirement                         Source-stated rule
  ----------------------------------- -----------------------------------
  Total credits                       Minimum 90, maximum 99

  Credits per level                   At least 30

  Subject-area credits                At least 24 credits from each of
                                      three subject areas, with grade C
                                      or better

  Minimum GPA                         2.00

  English requirement                 Pass ELPT I and ELPT II

  Completion period                   Within 5 academic years

  Level 4                             Not part of the standard three-year
                                      pathway
  -----------------------------------------------------------------------

### 3.2 B.Sc. Joint Major

The source describes this as a four-year pathway covering Levels 1--4.

  -----------------------------------------------------------------------
  Requirement                         Source-stated rule
  ----------------------------------- -----------------------------------
  Total credits                       Minimum 120, maximum 132

  Credits per level                   At least 30

  Major 1                             45 credits with grade C or better

  Major 2                             45 credits with grade C or better

  Minimum GPA                         2.00

  Selection criteria at end of Level  Overall GPA ≥ 2.5, pass ELPT I and
  2                                   II, and pass departmental interview

  Level 4 requirement                 Six-month industrial training

  Completion period                   Within 6 academic years
  -----------------------------------------------------------------------

The source lists these Joint Major combinations:

  Combination code   Major 1   Major 2   Level 1--2 subject
  ------------------ --------- --------- --------------------
  1A                 CMIS      ELTN      MATH & STAT
  1B                 CMIS      MMST      ELTN
  2A                 ELTN      CMIS      MATH & STAT
  2B                 ELTN      MMST      IMGT
  3A                 IMGT      ELTN      MATH & STAT
  3B                 IMGT      MMST      CMIS

**Unresolved naming:** `MMST` is reproduced as written in the
academic-flow source. The source does not provide enough evidence to
equate it with `MMOD`, or to identify a separate module-code prefix.
Confirm this mapping before implementing it in software.

### 3.3 B.Sc. Special

The source describes this as a four-year pathway covering Levels 1--4.

  -----------------------------------------------------------------------
  Requirement                         Source-stated rule
  ----------------------------------- -----------------------------------
  Total credits                       Minimum 120, maximum 132

  Credits per level                   At least 30

  Specialization credits              At least 72 credits from the
                                      specialization area, with grade C
                                      or better

  Minimum GPA                         2.00

  Selection criteria at end of Level  All registered module grades ≥ C;
  2                                   GPA conditions and departmental
                                      interview as described below

  Level 4 requirement                 Research project

  Completion period                   Within 6 academic years
  -----------------------------------------------------------------------

The supplied file lists these specializations:

1.  B.Sc. (Special) in Computer Science
2.  B.Sc. (Special) in Applied Electronics
3.  B.Sc. (Special) in Industrial Management
4.  B.Sc. (Special) in Mathematics with Statistics

The source's selection criteria state: - all grades for registered
modules are at least C; - overall GPA ≥ 2.5 and subject GPA ≥ 3.0,
**or** subject GPA ≥ 3.7 (the source also says overall GPA can be
2.5); - pass ELPT I and II; and - pass the departmental interview.

The wording of the alternative GPA condition is preserved from the
source and should be checked against the current official regulations
before being used for eligibility decisions.

## 4. Full module catalogue from the supplied tracker

**How to read this catalogue** - The module codes, titles, levels,
semesters, and credit values below are transcribed from
`wusl_module_tracker.md`. - A module's presence in this catalogue does
not prove that it is currently offered or compulsory for a particular
student. - The two Level 4 CMIS research-project codes contain
suspicious characters (`†`) in the source. They are preserved and
flagged for verification. - Module titles and code spellings have not
been silently changed to match assumptions.

### 4.1 Level 1 --- Semester I

  Module code   Module title                                        Credits
  ------------- ------------------------------------------------- ---------
  CMIS 1113     Introduction to Computers and Operating Systems           3
  CMIS 1123     Computer Programming I                                    3
  CMIS 1131     Practical Computing I                                     1
  ELTN 1112     Fundamentals of Electricity and Magnetism                 2
  ELTN 1122     Introduction to Semiconductors                            2
  ELTN 1132     Basic Digital Electronics                                 2
  MATH 1112     Introduction to Mathematics I                             2
  STAT 1113     Introduction to Probability and Statistics I              3
  IMGT 1112     Principles of Management                                  2
  IMGT 1122     Business Economics                                        2
  IMGT 1132     Entrepreneurial Dynamics                                  2

### 4.2 Level 1 --- Semester II

  Module code   Module title                                      Credits
  ------------- ----------------------------------------------- ---------
  CMIS 1212     Computer Programming II                                 2
  CMIS 1221     Practical Computing II                                  1
  ELTN 1212     Basic Electronics - Lab                                 2
  ELTN 1222     General Physics                                         2
  MATH 1212     Introduction to Mathematics II                          2
  MATH 1222     Differential Equations                                  2
  STAT 1213     Introduction to Probability and Statistics II           3
  IMGT 1212     Principles of Accounting                                2
  IMGT 1222     Marketing Management                                    2

### 4.3 Level 2 --- Semester I

  Module code   Module title                        Credits
  ------------- --------------------------------- ---------
  CMIS 2113     Object-oriented Programming               3
  CMIS 2123     Database Management Systems               3
  ELTN 2112     Electricity and Magnetism                 2
  ELTN 2121     Electricity and Magnetism - Lab           1
  MATH 2114     Linear Algebra I                          4
  STAT 2112     Statistical Inference I                   2
  IMGT 2112     Operations Management I                   2
  IMGT 2122     Cost & Management Accounting              2
  IMGT 2132     Service Industry Concepts                 2

### 4.4 Level 2 --- Semester II

  Module code   Module title                                 Credits
  ------------- ------------------------------------------ ---------
  CMIS 2214     Data Structures & Analysis of Algorithms           4
  ELTN 2213     Semiconductor Devices                              3
  ELTN 2221     Semiconductor Devices - Lab                        1
  ELTN 2232     Analogue Electronics                               2
  ELTN 2241     Analogue Electronics - Lab                         1
  MATH 2213     Linear Algebra II                                  3
  STAT 2212     Design of Experiments                              2
  STAT 2222     Regression Analysis                                2
  IMGT 2212     Human Resource Management                          2
  IMGT 2222     Operations Research I                              2

### 4.5 Level 3 --- Semester I

  Module code   Module title                                      Credits
  ------------- ----------------------------------------------- ---------
  CMIS 3114     Data Communication & Computer Networks                  4
  CMIS 3122     Rapid Application Development                           2
  CMIS 3134     Computer Architecture & Compiler Design                 4
  CMIS 3142     Computational Methods                                   2
  CMIS 3153     Advanced Database Systems                               3
  ELTN 3113     Digital Electronics                                     3
  ELTN 3121     Digital Electronics - Lab                               1
  ELTN 3133     Data Acquisition and Signal Processing                  3
  ELTN 3141     Data Acquisition and Signal Processing -- Lab           1
  MMOD 3113     Mathematical Methods                                    3
  MMOD 3124     Mathematical Models                                     4
  STAT 3112     Statistical Inference II                                2
  STAT 3124     Time Series Analysis                                    4
  IMGT 3112     Operations Management II                                2
  IMGT 3122     Organization Development                                2
  IMGT 3162     Business & Industrial Law                               2

### 4.6 Level 3 --- Semester II

  Module code   Module title                                            Credits
  ------------- ----------------------------------------------------- ---------
  CMIS 3214     Software Engineering                                          4
  CMIS 3224     Web Designing and e-commerce                                  4
  CMIS 3234     Computer Graphics and Visualization                           4
  CMIS 3242     Mobile and Ubiquitous Computing                               2
  CMIS 3253     Data Mining                                                   3
  ELTN 3212     AC Theory                                                     2
  ELTN 3222     Scientific Writing                                            2
  ELTN 3233     Microprocessor and Microcontroller Technology                 3
  ELTN 3241     Microprocessor and Microcontroller Technology - Lab           1
  MMOD 3214     Numerical Methods                                             4
  STAT 3212     Statistical Techniques                                        2
  STAT 3223     Operations Research                                           3
  STAT 3232     Data Analysis & Preparation of Statistical Reports            2
  IMGT 3212     Operations Research II                                        2
  IMGT 3222     Management of Technology                                      2
  IMGT 3232     International Business                                        2

### 4.7 Level 4 --- Semester I

  ------------------------------------------------------------------------
  Module code as   Module title                   Credits Validation note
  supplied                                                
  ---------------- ---------------- --------------------- ----------------
  CMIS 4114        Artificial                           4 Listed in
                   Intelligence                           tracker

  CMIS 4123        Advanced                             3 Listed in
                   Operating                              tracker
                   Systems                                

  CMIS 4134        Distributed and                      4 Listed in
                   Cloud Computing                        tracker

  CMIS 4142        Image Processing                     2 Listed in
                                                          tracker

  CMIS 4153        Parallel                             3 Listed in
                   Computing                              tracker

  CMIS 4+18        Research Project                     8 **Code appears
                   (Special)                              corrupted;
                                                          verify official
                                                          code**

  CMIS 4+26        Research Project                     6 **Code appears
                   (Joint Major)                          corrupted;
                                                          verify official
                                                          code**

  ELTN 4114        Communication                        4 Listed in
                   Theory and                             tracker
                   Systems                                

  ELTN 4143        Programmable                         3 Listed in
                   Logic Devices                          tracker

  ELTN 4151        Programmable                         1 Listed in
                   Logic Devices -                        tracker
                   Lab                                    

  MATH 4114        Complex                              4 Listed in
                   Variables                              tracker

  STAT 4114        Stochastic                           4 Listed in
                   Processes                              tracker

  STAT 4134        Actuarial                            4 Listed in
                   Mathematics                            tracker

  IMGT 4123        Environmental                        3 Listed in
                   Management based                       tracker
                   on ISO 14001                           

  IMGT 4133        Computer based                       3 Listed in
                   Modelling &                            tracker
                   Simulation                             

  IMGT 4142        Supply Chain                         2 Listed in
                   Management                             tracker

  IMGT 4152        Productivity                         2 Listed in
                   Techniques                             tracker

  IMGT 4162        Financial                            2 Listed in
                   Management                             tracker

  IMGT 4172        Strategic                            2 Listed in
                   Management                             tracker
  ------------------------------------------------------------------------

### 4.8 Level 4 --- Semester II

  Module code   Module title                                  Credits
  ------------- ------------------------------------------- ---------
  CMIS 4216     Industrial Training (Special)                       6
  INDT 4216     Industrial Training (General/Joint Major)           6
  ELTN 4213     Digital Signal Processing                           3
  MATH 4214     Partial Differential Equations                      4
  MATH 4224     Measure Theory                                      4
  IMGT 4213     Advanced Marketing Management                       3
  IMGT 4222     Applied Econometrics                                2
  IMGT 4234     Advanced Operations Research                        4
  IMGT 4242     Strategic Business Analysis                         2

## 5. Non-credit courses and auxiliary courses

The academic-flow document lists the following separately from the
module tables:

  -----------------------------------------------------------------------
  Code/name               Description             Notes
  ----------------------- ----------------------- -----------------------
  ELPC                    English Language        Described as compulsory
                          Proficiency Course      and non-credit in the
                                                  AttendTrack project
                                                  context; the
                                                  academic-flow document
                                                  refers to ELPT I and
                                                  ELPT II as tests. Do
                                                  not assume ELPC, ELPT
                                                  I, and ELPT II are
                                                  interchangeable labels.

  GAC                     General Auxiliary       Described as non-credit
                          Courses                 auxiliary courses in
                                                  the project
                                                  documentation; no
                                                  module-by-module list
                                                  is provided in these
                                                  two files.
  -----------------------------------------------------------------------

**Important:** The source uses both `ELPC` and `ELPT`. Their exact
relationship is not fully defined in the supplied documents. Keep them
as distinct terms until the faculty confirms their mapping.

## 6. Module-code handling and validation

The academic-flow document gives the example `CMIS 1123` and describes a
rough code pattern consisting of subject area, level, semester, module
sequence, and credits. Treat this as an explanatory pattern only; do not
rely on parsing every code by character position without validating the
official code.

### Required data-quality checks

1.  Store module code as a string; preserve spaces or normalize them
    only in a separate comparison key.
2.  Do not derive credits solely from the final digit of the code when
    the source data provides a credit value.
3.  Do not silently correct unknown characters or damaged codes.
4.  Flag `CMIS 4+18` and `CMIS 4+26` for manual verification.
5.  Keep `MMST` and `MMOD` distinct until their relationship is
    officially confirmed.
6.  Preserve source module title and source provenance.
7.  Distinguish a **module catalogue entry** from a **timetable
    session**. A module may have multiple lectures, tutorials,
    practicals, or groups.
8.  Do not infer a practical group from the module code. Practical
    groups are module-specific and should come from the current
    timetable/registration information.
9.  Do not assume that a module is applicable to a student's
    combination, major, or specialization merely because it appears in
    this catalogue.
10. If current official timetable data disagrees with this document,
    preserve the source values and flag the discrepancy for review
    rather than silently merging conflicting records.

## 7. Attendance-system implications (AttendTrack)

This section translates the supplied academic structure into safe
application rules. It is an implementation recommendation, not an
additional claim about official university policy.

### 7.1 Student academic profile

A profile should capture only the information required to determine the
student's timetable:

-   student/index number;
-   academic level;
-   academic year and semester;
-   Level 1--2 combination where applicable;
-   Level 3 General split where applicable;
-   Joint Major programme code and both majors where applicable;
-   Special degree specialization where applicable;
-   selected modules where the pathway requires explicit choices;
-   practical group assignment **per module**, not one global group.

### 7.2 Module catalogue vs timetable

Use these as separate entities:

-   **Module catalogue:** code, title, credits, subject area, source and
    verification status.
-   **Timetable revision:** source metadata/hash, academic year,
    semester, level and sync status.
-   **Timetable session:** module code, class type, date/day, start/end
    time, venue, group label and review state.
-   **Student module selection:** modules applicable to a particular
    student's academic profile.
-   **Student practical-group assignment:** one module-specific group
    choice per relevant module.

The supplied tracker alone does not provide session times, venues, class
types, current group labels, or a complete student-to-module eligibility
matrix. Those must come from current timetable data and confirmed
academic rules.

### 7.3 Recommended data source precedence

1.  **Current FAS timetable API** for current published sessions and
    source revision data.
2.  **Confirmed academic-structure rules** for student combinations and
    programme choices.
3.  **This supplied module tracker** as a reference catalogue and
    validation aid, subject to verification.
4.  Any unresolved conflicts should become review items; do not silently
    choose one version.

### 7.4 Timetable revision safety

-   Detect revisions using the upstream source's stable revision/hash
    metadata where available.
-   Keep the last known-good active timetable if a new fetch or
    validation fails.
-   Make sync idempotent.
-   Avoid using a timetable source session ID as a permanent attendance
    identity if IDs may change between revisions.
-   Do not erase historical attendance when the timetable changes.
-   Do not silently move an attendance record to a different session
    when the match is ambiguous.
-   Preserve ambiguous group/module data as `NEEDS_REVIEW` until
    resolved.
-   Use Asia/Colombo for timetable date boundaries.

### 7.5 Attendance calculation safety

The two supplied files describe an 80% attendance requirement in the
academic-flow and module-tracker content. This document does not
redefine the app's attendance formulas. Any weekly, monthly,
module-level, or overall attendance calculation must continue to follow
the app's approved attendance specification and existing tests.

## 8. GPA and academic rules present in the source files

AttendTrack's main purpose is attendance tracking; the following
information is included only because it appears in the supplied
documents. It should not be implemented as GPA or degree-progress
functionality unless that is separately approved.

### 8.1 Grade points listed by the tracker

  Grade     Mark range   Grade points
  ------- ------------ --------------
  A+           85--100            4.0
  A             70--84            4.0
  A-            65--69            3.7
  B+            60--64            3.3
  B             55--59            3.0
  B-            50--54            2.7
  C+            45--49            2.3
  C             40--44            2.0
  C-            35--39            1.7
  D+            30--34            1.3
  D             25--29            1.0
  E              0--24            0.0

The academic-flow source also lists `I` (Incomplete) as 0.0. The tracker
table does not include `I`. Confirm the current official grading rules
before using this table for any grade calculations.

### 8.2 GPA formula in the supplied tracker

`GPA = Σ(Credits × Grade Points) ÷ Σ(Credits)`

The source states that GPA is calculated to two decimal places. GPA
calculation is outside the primary attendance-tracking scope unless
explicitly added as a separate feature.

### 8.3 Attendance and eligibility statements

The academic-flow file says students must maintain 80% attendance to sit
end-semester examinations and states that a 30% weighted mean in
continuous assessment is also required. These are statements in the
supplied source, not independently verified current policy. Displaying a
student's attendance percentage is not the same as certifying official
examination eligibility.

## 9. Discrepancies and items requiring verification

  -----------------------------------------------------------------------
  Item                    What the files say      Recommended treatment
  ----------------------- ----------------------- -----------------------
  Research-project code 1 `CMIS 4+18` ---         Preserve as source text
                          Research Project        and flag; obtain
                          (Special), 8 credits    official code.

  Research-project code 2 `CMIS 4+26` ---         Preserve as source text
                          Research Project (Joint and flag; obtain
                          Major), 6 credits       official code.

  `MMST` vs `MMOD`        Joint Major table uses  Do not automatically
                          `MMST`; module          map them. Confirm
                          catalogue lists `MMOD`  official subject/major
                          and `STAT`              identifier.

  `ELPC` vs `ELPT`        Subject-code list       Keep distinct until the
                          includes ELPC; degree   faculty confirms their
                          requirements refer to   relationship.
                          ELPT I and II           

  Programme-to-module     Tracker lists modules   Do not assume each
  eligibility             by level and semester   module belongs to every
                          only                    programme or student
                                                  combination.

  Current module offering Tracker does not        Verify against current
                          include publication     timetable API and
                          dates or current        official registration
                          offering status         information.

  General split mappings  One example for COMB 1  Do not invent missing
                          is supplied             mappings for COMB 2/3.

  Module code pattern     A simplified code       Validate against actual
                          explanation is provided official codes; don't
                                                  derive critical fields
                                                  from code digits alone.

  Credit totals           Tracker presents a      Do not add all
                          catalogue across        catalogue credits and
                          multiple subjects, not  treat them as a
                          one student's           student's required
                          registered modules      credits.

  Timetable details       No session times,       Obtain these from the
                          venues, dates or        current timetable data.
                          current group           
                          assignments in tracker  
  -----------------------------------------------------------------------

## 10. Recommended verification workflow

1.  Fetch the current official FAS timetable data for the relevant
    academic year, semester and level.
2.  Validate each module code, title, and any available credit
    information against the supplied catalogue.
3.  Create a discrepancy report for missing, renamed, duplicated, or
    conflicting module entries.
4.  Verify damaged Level 4 project codes and the `MMST` naming issue
    with an official faculty source.
5.  Build programme/combination eligibility mappings only from a
    confirmed rule set; store mapping provenance.
6.  Keep timetable sessions separate from module catalogue records.
7.  Run tests for all combinations, degree pathways, module-specific
    practical groups, ambiguous records, timetable revisions, and users
    with incomplete setup.
8.  Do not change existing attendance calculations or historical
    attendance records while correcting academic mappings.

## 11. Scope boundary

This consolidated document is intended to support academic setup and
timetable matching for AttendTrack. It is **not** a replacement for the
current Faculty Prospectus, current module registration form, official
timetable, or faculty confirmation.

It intentionally does not: - invent missing modules; - infer unprovided
module-to-programme mappings; - repair corrupted module codes by
guessing; - treat every listed module as compulsory for every student; -
infer practical groups from a subject combination; - treat the
academic-flow examples as a complete eligibility matrix; or - introduce
GPA, results, credit tracking, or degree-progress functionality into
AttendTrack.

## 12. Source files

1.  `wusl_academic_flow.md` --- WUSL Faculty of Applied Sciences
    academic flow, combinations, degree pathways, and general academic
    rules. The file states that it is based on the WUSL Prospectus
    2020/2021 and was last updated in December 2024.
2.  `wusl_module_tracker.md` --- Module catalogue organized by Level
    1--4 and Semester I--II, with module titles and credits.

**Final status:** Consolidated and organized from both supplied files.
The documented transcription anomalies and incomplete mappings remain
explicitly flagged for official verification rather than being guessed.
