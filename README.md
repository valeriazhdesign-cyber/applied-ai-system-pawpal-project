# PawPal+ — AI-Assisted Pet Care Scheduler

## Original Project Identity

The original project is PawPal+, a pet-care planning assistant that began as a modular Python systems design exercise and evolved into a working scheduling app. Across Modules 1–3, it was designed to help a busy pet owner track recurring and one-off care tasks, respect time and priority constraints, and produce a clear daily plan with a human-readable explanation.

## Title and Summary

PawPal+ is a practical AI-assisted planner for pet owners who need a fast, reliable daily care schedule. Instead of treating every task as equally important, the system prioritizes urgent needs such as medication and feeding, identifies conflicts, and then explains its reasoning in a way that is easy for a person to review.

This matters because daily pet care is a real-world scheduling problem with trade-offs: time is limited, not all tasks are equally urgent, and some tasks repeat. PawPal+ turns that messy decision process into a structured, explainable plan.

## Project Overview

PawPal+ combines a deterministic scheduling engine with a lightweight retrieval-style AI layer. The scheduler receives owner preferences, pet information, and a list of tasks; it then filters, sorts, resolves conflicts, and assigns times. Before the final explanation is returned, the planner retrieves guidance from two local documents — a category-guidance JSON file and a per-species Markdown file — and merges the results into the rationale that appears alongside the schedule.

## Architecture Overview

The system diagram below shows the high-level architecture of the project:

```mermaid
flowchart LR
    A[Human Owner] --> B[Input: pet details, tasks, time budget, preferences]
    B --> C[Scheduler Core]
    C --> D[Conflict Detection + Priority Sorting]
    D --> E[Care Guidance Retriever]
    E --> F[Retrieved Pet-Care Context]
    F --> G[Plan Builder + Explanation Generator]
    G --> H[Final Schedule + AI Rationale]
    H --> I[Human Review / UI Check]
    I --> J[Testing and Validation]
    J --> K[Safe, Verified Output]
```

At a class level, the key components are:

- `Owner`: stores the person, time budget, preferences, and pets.
- `Pet`: holds the pet’s tasks and task-modifying behavior.
- `Task`: represents a single care action with duration, priority, recurrence, and timing data.
- `Scheduler`: owns the scheduling pipeline, conflict resolution, and plan generation.
- `CareGuidanceRetriever`: loads guidance from two independent local documents — `data/category_guidance.json` (task-category snippets) and `data/species_notes.md` (per-species care notes) — scores both against the current tasks/pets/preferences, and merges the results into the final explanation.
- `Plan`: captures the scheduled and skipped tasks and the narrative explanation returned to the user.

## Setup Instructions

1. Clone the repository and move into the project directory.
2. Create a fresh virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the CLI demo:

```bash
python3 main.py
```

5. Run the test suite:

```bash
python3 -m pytest -q
```

6. Launch the Streamlit app for a browser-based UI:

```bash
streamlit run app.py
```

## Sample Interactions

Every example below is real output copied from an actual run (ANSI color codes stripped for readability), not a paraphrase — commands are shown so you can reproduce each one.

### Example 1 — End-to-end run: build today's schedule

Command:
```bash
python3 main.py
```

Input (hardcoded in `main.py` for the demo): Owner Valeria, 120 available minutes, two pets (Rex the dog, Luna the cat), 8 tasks across walk/feeding/meds/grooming/enrichment categories, one already completed, two pairs of tasks with overlapping `preferred_time`.

Output (first section of the run):
```text
──────────────────────────────────────────────────────
  📅  TODAY'S SCHEDULE
──────────────────────────────────────────────────────
  Owner: Valeria  |  Budget: 120 min

╭────────┬───────────────────┬────────┬────────────┬────────────╮
│ Time   │ Task              │ Pet    │ Priority   │ Duration   │
├────────┼───────────────────┼────────┼────────────┼────────────┤
│ 07:00  │ 🦮 Morning Walk    │ 🐕 Rex  │ ● HIGH     │ 30 min     │
│ 07:30  │ 🍽️ Breakfast      │ 🐕 Rex  │ ● HIGH     │ 10 min     │
│ 08:00  │ 💊 Flea Medication │ 🐕 Rex  │ ◑ MED      │ 5 min      │
│ 09:00  │ ✂️ Brush Coat     │ 🐈 Luna │ ◑ MED      │ 15 min     │
│ 09:30  │ 🎾 Feather Wand    │ 🐈 Luna │ ○ LOW      │ 20 min     │
╰────────┴───────────────────┴────────┴────────────┴────────────╯

  Scheduled 5 task(s) using 80/120 available minutes.

Guidance:
- An early walk burns energy and reduces destructive behavior later in the day.
- Medication tasks should stay near the front of the day because missed doses carry the highest health risk.
- Feeding tasks cover basic nutrition needs and should be preserved before optional enrichment tasks.
```
Vet Call (Rex, 07:10) and Nail Trim (Luna, 09:10) are absent from this table — both were dropped earlier in the pipeline by conflict resolution because they overlapped a higher-priority task that already claimed the slot (see the guardrail example below for the warnings that explain this).

### Example 2 — AI feature: multi-source retrieval (RAG-style)

Command:
```bash
python3 -c "
from pawpal_system import CareGuidanceRetriever, Category, Owner, Pet, Task, Priority
owner = Owner('Jordan', available_minutes=60)
rex = Pet('Rex', species='dog')
owner.add_pet(rex)
walk = Task('Morning Walk', Category.WALK, duration=20, priority=Priority.HIGH, preferred_time='07:00')
rex.add_task(walk)
for line in CareGuidanceRetriever().retrieve([walk], owner, top_k=3):
    print('-', line)
"
```

Input: one dog (Rex), one WALK-category task, no preferences.

Retrieval used to pull from a single JSON document of category-guidance snippets. Adding a second document — `data/species_notes.md`, parsed into per-species care notes — and merging both sources at query time changed the output for this exact input:

**Before** (category source only, one match):
```text
- An early walk burns energy and reduces destructive behavior later in the day.
```

**After** (category + species sources merged — actual output of the command above):
```text
- An early walk burns energy and reduces destructive behavior later in the day.
- Dogs are highly exercise-driven; consistent daily walks reduce anxiety and destructive behavior more than almost any other single intervention.
```

The category snippet and the species note score independently (2 points each here) and are ranked together, so the explanation now grounds its reasoning in both *what kind of task this is* and *what kind of pet it's for* — a genuinely richer rationale than either source alone, without adding any external API or database. See [Design Decisions](#design-decisions) for how the two documents are combined.

### Example 3 — Recurrence handling

Command: same `python3 main.py` run as Example 1; this is a later section of the same output.

Input: `Morning Walk` is a `daily` recurring task with `last_done=None`, marked complete for today (2026-08-03).

Output:
```text
──────────────────────────────────────────────────────
  🔄  RECURRING RESCHEDULE DEMO
──────────────────────────────────────────────────────
  Before:  Morning Walk  completed=⏳ pending  last_done=None
  After:   Morning Walk  completed=✅ done  last_done=2026-08-03

╭─────────────────┬──────────────┬────────────╮
│ Next occurrence │ Morning Walk │ ⏳ pending  │
│ is_due today    │ —            │ False      │
│ days_until_next │ —            │ 1 day(s)   │
│ next_due_date   │ —            │ 2026-08-04 │
╰─────────────────┴──────────────┴────────────╯

  Rex now has 5 tasks (new occurrence appended)
```
The original task is stamped `completed=True, last_done=2026-08-03`; a fresh pending copy is appended for the next cycle; and `is_due("2026-08-03")` on that new copy correctly returns `False`, so it will not reappear in the same-day plan.

### Example 4 — Reliability guardrails + automated evaluation

**Guardrail 1 — conflict resolution and time-budget skip, working together.** Command:
```bash
python3 -c "
from pawpal_system import Category, Owner, Pet, Priority, Scheduler, Task
owner = Owner('Jordan', available_minutes=30, preferences='morning routine')
mochi = Pet('Mochi', species='cat')
owner.add_pet(mochi)
mochi.add_task(Task('Morning Walk', Category.WALK, duration=30, priority=Priority.HIGH, preferred_time='07:00'))
mochi.add_task(Task('Give Medication', Category.MEDS, duration=10, priority=Priority.HIGH, preferred_time='07:00'))
mochi.add_task(Task('Breakfast', Category.FEEDING, duration=10, priority=Priority.HIGH, preferred_time='07:40'))
mochi.add_task(Task('Brush Coat', Category.GROOMING, duration=15, priority=Priority.MEDIUM, preferred_time='08:00'))
scheduler = Scheduler(owner, start_time='07:00')
pet_map = {id(t): mochi for t in mochi.tasks}
plan = scheduler.generate_plan(mochi.tasks, pet_map=pet_map, today='2026-08-03')
print(plan.display())
"
```

Input: an owner with only 30 available minutes and four tasks that together need 65 minutes, two of which (Morning Walk and Give Medication) are both scheduled for 07:00.

Output (actual):
```text
=== Care Plan for Jordan ===
Total scheduled time: 30 min

Scheduled:
  [HIGH] Morning Walk (Mochi) @ 07:00 (30 min)

Skipped:
  Breakfast — insufficient time remaining
  Brush Coat — insufficient time remaining

Warning: 65 min requested, only 30 min available — some tasks will be skipped.
Scheduled 1 task(s) using 30/30 available minutes.

Guidance:
- An early walk burns energy and reduces destructive behavior later in the day.
- Cats are routine-sensitive and often mask illness; sudden changes in feeding or litter schedules are a common early warning sign worth watching for.
```
Two guardrails fire here, visibly: `handle_conflicts` silently drops "Give Medication" before scheduling even starts because it overlaps the higher-priority Morning Walk slot (the same mechanism that produced the conflict warnings in Example 1), and the time-budget check then skips "Breakfast" and "Brush Coat" with an explicit reason and an explicit warning, rather than silently truncating the plan or crashing on an over-budget input.

**Guardrail 2 — automated evaluation (test suite).** Command:
```bash
python3 -m pytest -q
```
Output (actual):
```text
.........................                                                [100%]
25 passed in 0.01s
```
The suite covers sorting, recurrence, conflict detection/resolution, and every `CareGuidanceRetriever` behavior exercised above (category matching, species-note merging, `top_k` limiting, and the no-match case where `build_rationale` must return the base explanation unchanged) — see [Testing Summary](#testing-summary) for the full breakdown.

## Design Decisions

The main design decision was to keep the system modular and explainable. Instead of building one opaque “AI box,” the project separates the logic into clear pipeline stages: input collection, task sorting, conflict detection, recurrence filtering, time allocation, and final explanation generation.

That architecture makes the system easier to test and easier for a future engineer to extend. I also chose a small, deterministic retrieval layer rather than a heavyweight external model because it keeps the project reproducible, inexpensive, and stable for a classroom or portfolio context.

The trade-off is that the retrieval layer is intentionally simple. It is not a large knowledge engine, and it does not perform deep semantic search across a real database. In return, it provides a clear, reliable improvement to the explanation quality without adding fragile dependencies.

**Multiple data sources.** `CareGuidanceRetriever` originally scored a single hardcoded list of category snippets embedded in Python. It now loads two independent local documents at construction time — `data/category_guidance.json` (structured, keyed by `Task.category`) and `data/species_notes.md` (unstructured prose, one `## <species>` section per pet species, parsed at load time) — and scores both against the current tasks, pets, and preferences before merging them into a single ranked list (see [Example 2](#example-2--ai-rationale-path-multi-source-retrieval) for a before/after run). This was a deliberate two-source design rather than one bigger document: category guidance answers "what kind of task is this," species notes answer "what kind of pet is this for," and an owner with multiple pets of the same species sees that species' note ranked higher (the score scales with pet count) — something a single category-only source has no way to express. Adding a third source (e.g., an owner-preference document) would only require another loader method and a few more scored tuples in `retrieve()`.

## Testing Summary

The test suite confirms the central scheduling behaviors are working as intended:

- tasks sort correctly by time and priority,
- recurring tasks queue the next occurrence correctly,
- completion state is handled safely,
- conflicts are detected and resolved in a deterministic order,
- the `CareGuidanceRetriever` surfaces the right snippet for a task's category, respects its `top_k` limit, leaves the explanation untouched when nothing matches, merges its two guidance documents into one ranked list, and scales a species note's rank with how many pets of that species the owner has.

I also learned that reproducibility matters as much as cleverness. A project that cannot be re-run easily by another developer is not a strong portfolio piece. A stable dependency list and a single CLI entrypoint (`main.py`) both contribute to that reliability — while finishing this write-up I actually caught a broken import in `main.py` (a stray `cd` had been typed in front of the `datetime` import) that would have failed for anyone cloning the repo; running the CLI end-to-end before publishing is what caught it.

The retrieval feature is intentionally lightweight: 25 tests cover the scheduler and the `CareGuidanceRetriever` (category-match scoring, top-k limiting, rationale building, and merging the JSON and Markdown guidance sources), and I additionally exercised the Streamlit app manually to confirm the guidance text renders correctly in the UI, not just in tests. It is not an external knowledge base or a full production RAG system — it is two small, fixed local documents scored by category and species overlap. That is a sensible trade-off for a project whose primary value is scheduling logic and explainability.

## Reflection

This project taught me that AI is most effective when it supports a clear human workflow rather than replacing it. A good system does not just “generate text”; it retrieves relevant context, uses it to make a decision, and then returns an output that a person can inspect and trust. That principle guided the design of PawPal+.
