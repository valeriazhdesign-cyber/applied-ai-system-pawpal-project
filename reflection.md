# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

3 core tasks:
1. Add/configure a pet (and owner) profile
2. Add and manage care tasks
3. Generate and view today's plan

- Briefly describe your initial UML design.

Owner
Attributes: name, pets (list of Pet)
Methods: add_pet(pet)

Pet
Attributes: name, species, breed, tasks (list of Task)
Methods: add_task(task), remove_task(task)

Task
Attributes: name, category (walk/feeding/meds/etc.), duration (minutes), priority (high/med/low), preferred_time (optional)
Methods: __repr__() for clean display

Scheduler
Attributes: available_minutes, maybe start_time
Methods: generate_plan(tasks) → returns a Plan, plus helpers like sort_by_priority(), filter_by_time()

Plan
Attributes: scheduled_tasks (list), skipped_tasks (list), explanation
Methods: display()


- What classes did you include, and what responsibilities did you assign to each?

Owner — represents the human user and hold the link to their pet. It stores owner info, maintain the collection of pets.

Pet — the anchor that care tasks attach to. It stores the pet's identity (name, species, breed) and manage its own list of tasks (add/remove).

Task — describes a single care activity and its schedulin relevant data.

Scheduler — takes a set of tasks plus constraints (available time, priorities) and decide what gets scheduled, in what order, and what gets dropped. 

Plan — holds the output of the Scheduler: the ordered list of scheduled tasks, any skipped tasks, and the reasoning.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
1. Plan has no link back to Owner or Pet
- Owner.all_tasks() added (pawpal_system.py:79)

New method that returns list[tuple[Pet, Task]] — every task across all pets, paired with its pet so context isn't lost
- Plan.__init__ signature changed (pawpal_system.py:86)

Was: __init__(self)
Now: __init__(self, owner: "Owner", pet: Optional["Pet"] = None)
Stores both on self, so a plan always knows whose it is and which pet it covers (or None for a multi-pet plan)
2. Scheduler reads available_minutes from... itself, not Owner
Scheduler.__init__ signature changed (pawpal_system.py:102)
Was: __init__(self, available_minutes: int, ...)
Now: __init__(self, owner: "Owner", ...) — stores the owner and derives available_minutes from it rather than duplicating the value
3. No multi-pet aggregation path
Scheduler.generate_plan signature changed (pawpal_system.py:106)
Added optional pet parameter so the generated plan can be tagged to a specific pet when relevant
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?
- Priority (Priority.HIGH / MEDIUM / LOW) — tasks are sorted highest-first before anything else; when two tasks conflict for the same slot, the higher-priority one wins
- Preferred time (preferred_time) — tasks before start_time are dropped by filter_by_time; assign_times snaps each task to its preferred slot rather than packing back-to-back
- Available minutes — acts as a hard cap; tasks that would exceed the owner's time budget are moved to skipped_tasks
- Completion status — already-completed tasks are filtered out by filter_by_status so they never re-appear in the plan
- Recurrence window (recurring + last_done) — filter_by_recurrence drops daily tasks already done today and weekly tasks done within the past 7 days

Priority was placed first because the consequences are unequal — missing a HIGH task like medication has a real impact on the pet, while missing a LOW enrichment task does not. Time constraints come second because a task outside the available window is irrelevant regardless of priority. Available minutes acts last as a hard cap since it is an absolute physical constraint the owner cannot override.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

When two tasks overlap in time, the scheduler just drops the lower-priority one instead of trying to move it to a new time slot. In handle_conflicts, if a lower-priority task's preferred time overlaps with a higher-priority task that already took that slot, it gets removed from the plan and logged in skipped_tasks.
A fancier approach would try to bump the conflicting task to the next open slot. But that gets messy fast — moving one task could bump into another task, which bumps another, and so on. That's a lot of extra complexity for something as simple as a daily pet care schedule.
Dropping conflicts makes more sense here because pet care is time-sensitive. A 7 AM walk isn't really a "7 AM walk" anymore if it happens at 11 AM. Instead of silently moving tasks to random open times (which might not even make sense for the pet), it's better to flag the conflict with detect_conflicts and let the owner decide what to do.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used Claude Code across three distinct phases, each in a separate chat session.

**Phase 1 — Design brainstorming.** Before writing any code, I described the problem domain ("a pet care scheduler with priorities, time constraints, and recurrence") and asked the AI to critique my initial five-class UML. The most effective prompts were *constraint-setting* ones: "Given that this runs as a daily planner — not a calendar app — which classes are doing too much?" That framing helped surface that `Scheduler` should not own `available_minutes` independently when `Owner` already did.

**Phase 2 — Implementation.** The most effective feature was autocomplete on method stubs. Once I drafted the docstring for `filter_by_recurrence` and `is_due`, the AI filled in the boundary conditions (daily vs. weekly cadence, `last_done` is None) faster than I could have typed them. Asking "What edge cases should this method handle?" before writing code consistently produced a shorter to-do list than discovering them during testing.

**Phase 3 — Test generation.** Prompts of the form "Generate pytest cases for `handle_conflicts` assuming tasks are already sorted by priority" were highly effective. They pushed the AI to write tests that matched the function's documented precondition rather than testing the sort order again.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

When I asked the AI to implement `handle_conflicts`, it initially returned a version that both removed lower-priority tasks *and* added them to `plan.skipped_tasks` directly — mixing two responsibilities in one method. The method would have been impossible to unit-test without constructing a `Plan` object, and it violated the single-responsibility principle I had set up: `Scheduler` methods should return clean task lists; only `generate_plan` should call `plan.add_skipped`.

I rejected that version and asked instead: "Rewrite `handle_conflicts` so it only returns a filtered list and does not touch the Plan. The caller in `generate_plan` will handle skipping." The revised version matched the pipeline pattern already used by `filter_by_status` and `filter_by_recurrence`, so it slotted in cleanly at `pawpal_system.py:287`.

I verified the fix by tracing the call chain in `generate_plan` manually and confirming that `plan.add_skipped` is only called in one place (the final time-budget loop at line 298–304), keeping the skipping logic centralized and auditable.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

The test suite covers four behavioral clusters:

1. **Task lifecycle** — `mark_complete` sets `completed=True`, records `last_done`, and is idempotent. `complete_task` on a recurring task appends a fresh pending copy to the pet's list. These tests matter because the recurrence pipeline depends on `completed` and `last_done` being set correctly; a silent mutation bug here would cause tasks to disappear from future schedules.

2. **Sorting correctness** — `sort_by_priority` returns HIGH → MEDIUM → LOW; `sort_by_time` returns chronological order with untimed tasks at the end. These are the first two steps of `generate_plan`'s pipeline; if either sort is wrong, everything downstream is wrong.

3. **Recurrence filtering** — `is_due` returns False for a daily task completed today, True for one completed yesterday, and handles the weekly 7-day boundary exactly. These boundary conditions are the most error-prone part of the scheduler — off-by-one errors here would either spam the owner with already-done tasks or silently skip due ones.

4. **Conflict detection and time-budget enforcement** — `detect_conflicts` flags overlapping windows; `generate_plan` schedules tasks that fit and skips ones that exceed `available_minutes`. These tests confirm the core contract the UI depends on: the `Plan` object is always internally consistent.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

High confidence for the core scheduling pipeline — every filter and sort step has direct unit tests, and the happy-path `generate_plan` call is covered end-to-end.

Edge cases I would add next:
- **Zero available minutes** — does `generate_plan` skip all tasks gracefully without crashing?
- **All tasks at the same preferred time** — `handle_conflicts` keeps the first (highest-priority) one, but the others currently disappear silently rather than appearing in `skipped_tasks`.
- **`preferred_time` before `start_time`** — tasks filtered by `filter_by_time` are also silently dropped; they should probably land in `skipped_tasks` with a reason like "before start time".
- **Multi-pet plans where two pets share the same task time** — `detect_conflicts` already handles cross-pet warnings, but this path has no dedicated test.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The pipeline architecture in `generate_plan` (sort → filter_by_time → filter_by_status → filter_by_recurrence → handle_conflicts → assign_times → budget loop). Each step is a pure function that takes a list and returns a list, which made it trivial to test any stage in isolation and easy to read the overall algorithm top-to-bottom. When I decided to add `filter_by_recurrence` late in the project, it dropped into the pipeline without touching any other method.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

The skipping logic is the weakest part of the current design. Tasks can be removed silently by `filter_by_time` (before start), `filter_by_status` (already done), or `handle_conflicts` (time overlap), and none of those paths add an entry to `skipped_tasks`. The owner gets no explanation for why a task vanished. I would redesign those three methods to return `(kept, skipped_with_reason)` tuples so `generate_plan` can always give the owner a full accounting — every task either scheduled or explicitly explained.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

**Separate chat sessions per phase are a forcing function for clarity.** Because the design session had no knowledge of the implementation, I had to articulate class responsibilities in plain language, not code. That friction exposed two ambiguities before a single line was written: who owns `available_minutes`, and whether `Plan` needs a back-reference to `Owner`. Catching those in a diagram is much cheaper than refactoring them out of real code.

The broader lesson: powerful AI tools reward architects who *know what they want before they ask*. When I gave the AI a precise contract ("return a filtered list; no side effects"), it produced code I could use. When I gave it an outcome ("handle conflicts"), it produced code that mixed concerns. The AI doesn't know your design constraints — it knows common patterns. Your job as lead architect is to supply the constraints so the AI's pattern-matching lands in the right design space, then verify that it actually did.
