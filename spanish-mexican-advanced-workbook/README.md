# Spanish Mexican Dialect — Advanced Workbook (B2/C1)

An interactive, Python-based workbook for practicing advanced Mexican Spanish through translation and typing exercises. Over 1,000 exercises with retry logic, progress tracking, and analytics.

> **Who this is for.** You already speak conversational Spanish (B1+) and want to push into B2/C1 territory with a focus on the Mexican dialect. You learn best by doing — translating, typing, and self-correcting.

---

## Why this course

Most Spanish resources teach "standard" Spanish and sprinkle in regional notes as an afterthought. This workbook is different:

- **Mexican Spanish first.** Every exercise uses Mexican vocabulary, phrasing, and conventions (e.g., *¿Mande?*, *órale*, *neta*, *luego luego*, double object pronouns the Mexican way).
- **Type it out.** You translate, type, and compare. Muscle memory beats recognition.
- **Retry on wrong answers.** Get it wrong? You get one retry. Miss twice and the answer is revealed — then move on.
- **Progress tracking.** Every attempt is saved to a local SQLite database. Run analytics to see your weak spots, mastery levels, and learning trends.
- **Advanced grammar focus.** Subjunctive mood, *se lo/se la*, indirect/direct object reference, irregular verb forms, and more — the stuff that separates B2 from C1.

---

## Topics covered

| #  | Lesson | Focus | Est. |
|----|--------|-------|------|
| 01 | [Subjunctive Mood — Present](./lessons/01_subjunctive_present.py) | Present subjunctive in noun clauses, volitional verbs, emotion, doubt, impersonal expressions | 1.5 h |
| 02 | [Subjunctive Mood — Past](./lessons/02_subjunctive_past.py) | Imperfect subjunctive, conditional sentences (si clauses), past wishes/regrets | 1.5 h |
| 03 | [Double Object Pronouns — "Se lo/Se la"](./lessons/03_se_lo_se_la.py) | Replacing IO+DO with *se lo/se la/se los/se las*, placement, redundancy with *a* phrases | 1.5 h |
| 04 | [Indirect & Direct Object Reference](./lessons/04_object_reference.py) | "He told her", "The woman gave him", *le* vs *lo*, clarifying *a + pronoun*, Mexican usage patterns | 2 h |
| 05 | [Irregular Verbs — Stem-Changing & Orthographic](./lessons/05_irregular_verbs.py) | *dormir→duerma*, *sentir→sienta*, *c-z-g* spelling changes in subjunctive, go-verbs, *y* verbs | 1.5 h |
| 06 | [Irregular Verbs — Fully Irregular & Idiomatic](./lessons/06_irregular_verbs_advanced.py) | *ir*, *ser*, *haber*, *saber*, *caber*; Mexican idiomatic verb phrases (*echar*, *darle*, *ponerse*) | 1.5 h |
| 07 | [Subjunctive in Adjective & Adverbial Clauses](./lessons/07_subjunctive_clauses.py) | Relative clauses with unknown antecedent, *para que*, *aunque*, *en cuanto*, *sin que* | 1.5 h |
| 08 | [Perfect Tenses & Past Participle Irregularities](./lessons/08_perfect_tenses.py) | Present perfect, past perfect, future perfect, conditional perfect; irregular past participles (*abierto, escrito, muerto*) | 1 h |
| 09 | [Mexican Dialect & Cultural Nuances](./lessons/09_mexican_dialect.py) | *¿Mande?*, *órale/híjole*, diminutives, *neta*, *luego luego*, *chido/ padre*, *ahorita* ambiguity, Mexican voseo absence | 1.5 h |
| 10 | [Capstone — Mixed Translation Drills](./lessons/10_capstone.py) | Everything combined: subjunctive + double pronouns + irregulars + Mexican expressions in context | 2 h |

**Total: ~16 hours of focused practice, 1,000+ exercises.**

---

## How it works

Each lesson is a standalone Python script. Run it, and it becomes an interactive workbook:

```bash
cd spanish-mexican-advanced-workbook
python3 lessons/01_subjunctive_present.py
```

For each question you will:
1. See an English prompt or a fill-in-the-blank Spanish sentence
2. Type your Spanish translation (or pick from choices for MC)
3. If wrong, you get **one retry** — try again
4. If wrong twice, the correct answer is revealed
5. See an explanation after each question
6. Get a detailed score breakdown at the end

### Retry logic

- **First try correct** → marked as mastered
- **Wrong once, correct on retry** → marked as learning
- **Wrong twice** → answer revealed, marked as a weak spot

The lessons use **fuzzy matching** — minor accent or punctuation differences won't count against you, but you need to get the core grammar and vocabulary right.

---

## Progress tracking & analytics

Every attempt is saved to `progress.db` (SQLite, stored in this directory). View your analytics:

```bash
python3 code/analytics.py
```

The analytics dashboard shows:

- **Overall progress** — total attempts, first-try accuracy, 95% confidence intervals
- **Per-lesson breakdown** — mastery level per topic with visual progress bars
- **Weak spots** — questions you consistently miss, ranked by difficulty
- **Learning trends** — accuracy over time, improving/declining indicators
- **Retention** — questions revisited across sessions
- **Mastery levels** — Mastered / Learning / Struggling classification per question
- **Spaced repetition suggestions** — which questions to review next
- **Statistical summary** — accuracy rates, standard errors, confidence intervals, strongest/weakest lessons

---

## Prerequisites

- Python 3.8+ (no external packages needed)
- Solid B1 Spanish: you can hold a basic conversation, conjugate present/preterite/imperfect, and know common vocabulary
- Familiarity with the Mexican dialect basics (*tú* not *vos*, *¿mande?*, common slang)

---

## Quick start

```bash
cd spanish-mexican-advanced-workbook
python3 lessons/01_subjunctive_present.py
```

Run `VERIFY.md` checks first if you want to confirm your Python setup:

```bash
python3 -c "print('Python OK')"
```

After completing lessons, check your analytics:

```bash
python3 code/analytics.py
```

---

## Project structure

```
spanish-mexican-advanced-workbook/
├── README.md
├── VERIFY.md
├── GLOSSARY.md
├── progress.db                ← auto-created SQLite tracking DB
├── requirements.txt
├── lessons/
│   ├── 01_subjunctive_present.py
│   ├── 02_subjunctive_past.py
│   ├── 03_se_lo_se_la.py
│   ├── 04_object_reference.py
│   ├── 05_irregular_verbs.py
│   ├── 06_irregular_verbs_advanced.py
│   ├── 07_subjunctive_clauses.py
│   ├── 08_perfect_tenses.py
│   ├── 09_mexican_dialect.py
│   └── 10_capstone.py
└── code/
    ├── workbook_engine.py     ← shared exercise engine (retry logic, scoring, DB)
    └── analytics.py           ← learning analytics dashboard
```

Ready? **→ [Start with Lesson 01: Subjunctive Mood — Present](./lessons/01_subjunctive_present.py)**