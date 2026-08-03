# Model Card: PawPal+ Responsible-AI Reflection

## Project Summary

PawPal+ is a pet-care planning assistant that uses rule-based scheduling with a deterministic retrieval layer (`CareGuidanceRetriever`) for its explanations. The retriever merges two local documents — a category-guidance JSON file and a per-species Markdown file — to ground the plan's rationale in both task type and pet type. The system is designed to help a busy owner turn a set of pet-care tasks into a realistic daily schedule while also explaining why some tasks rank higher than others.

## Limitations and Biases

The scheduler has no real "understanding" of pet care — it is priority sorting, category-weighted scoring, and interval overlap checks over data the owner types in. It trusts that input at face value: if someone mislabels a trivial task as HIGH priority or `meds`, the system has no way to detect that and will schedule and explain it as if it were urgent. There is no validation layer that checks task data against anything external.

The urgency model also encodes a fixed value judgment: `Task.weighted_score()` hardcodes category urgency as meds > feeding > walk > grooming > enrichment, and the category side of `CareGuidanceRetriever` matches on that same fixed list. That ordering is a reasonable default but is not universal — a diabetic cat's grooming-adjacent skin check could matter more than a healthy dog's walk, and the system has no way to represent that nuance. Moving the guidance from a hardcoded Python list into two local documents (`data/category_guidance.json`, `data/species_notes.md`) makes it easier to extend without touching code, but the coverage is still small and fixed — 5 categories and 3 species notes — so any task category or pet species outside those documents silently gets no guidance at all rather than a fallback or a "no guidance available" note.

Because everything is deterministic and rule-based, the system is transparent and reproducible, but it does not generalize — it is a good fit for a known, bounded set of routine daily-care tasks and a poor fit for anything resembling real veterinary judgment.

## Potential for Misuse and Mitigations

The realistic misuse risk isn't adversarial (this is a single-owner scheduling tool, not a shared or adversarial system) — it's an over-trust risk. The retrieved guidance sentences (e.g., "Medication tasks should stay near the front of the day because missed doses carry the highest health risk.") read like considered advice, and a user could mistake them for actual veterinary guidance rather than a canned, category-matched heuristic with no clinical review behind it. Someone could lean on PawPal+'s scheduling for a genuinely sick or high-needs pet and delay a real vet consultation because the app's "explanation" sounded authoritative.

Mitigation: the guidance text should always be framed as scheduling rationale, not medical advice, and a future version should carry an explicit disclaimer in the UI (e.g., in `app.py`, near where `plan.explanation` is rendered) stating that PawPal+ is a scheduling aid, not a substitute for veterinary care. I did not add a UI disclaimer in this pass — that is a concrete follow-up rather than a solved problem.

## Surprises While Testing Reliability

The biggest surprise was that the project's own documentation had drifted completely away from the code. The README, this model card, and the UML diagram all described a `CareGuidanceRetriever` retrieval layer in specific, confident detail — but grepping `pawpal_system.py`, `app.py`, and `main.py` for `CareGuidanceRetriever`, `retrieve`, and `rationale` turned up nothing. The class had never been implemented; only its description existed. That is a direct lesson about AI-assisted documentation: confident, detailed prose is not evidence that a feature exists, and docs have to be checked against the real source before they're trusted or published.

A second, smaller surprise: `main.py` had a broken first line (`cdfrom datetime import date` — a stray `cd` typed in front of the import) that would have crashed the CLI demo for anyone who cloned the repo and ran it. It had gone unnoticed because nobody had actually re-run `python3 main.py` after that line was last touched. Running every entry point end-to-end (CLI, pytest, and the Streamlit app in a live browser session) before writing the "this works" documentation is what caught both problems, and reinforced that testing a written description of behavior is not the same as testing the behavior itself.

## AI Collaboration: Helpful and Flawed Suggestions

I used AI as a design and debugging partner throughout the build, and again when preparing this documentation. The most useful collaboration pattern was asking for a narrow, falsifiable check ("does this class actually exist?", "does this method do what the docstring says?") rather than accepting a summary at face value.

**Helpful suggestion:** Refactoring `generate_plan()` into a clean, explicit sequence of pipeline stages — sort, filter by time, filter by status, filter by recurrence, resolve conflicts, assign times — made the scheduling logic far easier to inspect, test, and extend. It also reduced the chance that one stage would accidentally mutate state meant for another, and it's the reason `CareGuidanceRetriever` could be dropped into the pipeline as one more explicit step without disturbing the rest.

**Flawed suggestion:** Earlier AI-authored drafts of the README, this model card, and the UML diagram described `CareGuidanceRetriever` as an already-implemented retrieval-style AI layer, complete with specific example output. It was entirely fabricated relative to the actual codebase — no such class existed anywhere. Had I published those drafts as-is, the portfolio would have claimed a capability the system didn't have. I caught it by grepping the source for the class name before trusting the docs, and resolved it by building the retriever for real (wiring it into `Scheduler.generate_plan()`, adding 6 tests, and verifying the guidance text renders correctly in both the CLI and a live Streamlit session) rather than just softening the claims.
