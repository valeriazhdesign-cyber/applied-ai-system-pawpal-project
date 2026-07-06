# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

```
$ python3 main.py
=============================================
         PAWPAL — TODAY'S SCHEDULE
=============================================
=== Care Plan for Valeria ===
Total scheduled time: 75 min

Scheduled:
  [HIGH] Morning Walk (Rex) @ 07:00 (30 min)
  [HIGH] Breakfast (Rex) @ 07:30 (10 min)
  [MEDIUM] Brush Coat (Luna) @ 09:00 (15 min)
  [LOW] Feather Wand (Luna) @ 09:30 (20 min)

Scheduled 4 task(s) using 75/120 available minutes.
```

> Wet Food (Luna) was already completed before the schedule ran. Vet Call (Rex) and Nail Trim (Luna) were dropped by conflict resolution — both overlapped a higher-priority task that had already claimed the time slot.

## 📋 CLI Output: Priority-Based Scheduling

These examples show how the enhanced scheduler differs from simple time-based ordering.

### 1 — Sort by time vs sort by priority

Time-based sorting puts tasks in clock order, regardless of importance.
Priority-based sorting ensures the most critical tasks appear first so they are
never bumped by a time budget cut.

```
=============================================
  SORTED BY TIME (all tasks)
=============================================
  07:00  Morning Walk (Rex)
  07:10  Vet Call (Rex)
  07:30  Breakfast (Rex)
  08:00  Flea Medication (Rex)
  08:15  Wet Food (Luna)
  09:00  Brush Coat (Luna)
  09:10  Nail Trim (Luna)
  09:30  Feather Wand (Luna)

=============================================
  SORTED BY PRIORITY (all tasks)
=============================================
  [HIGH]  Morning Walk (Rex)
  [HIGH]  Vet Call (Rex)
  [HIGH]  Breakfast (Rex)
  [HIGH]  Wet Food (Luna)
  [MEDIUM]  Flea Medication (Rex)
  [MEDIUM]  Brush Coat (Luna)
  [MEDIUM]  Nail Trim (Luna)
  [LOW]  Feather Wand (Luna)
```

Within the same priority level ties are broken by `preferred_time` (converted to
minutes), so earlier-timed HIGH tasks still appear before later-timed HIGH tasks.

### 2 — Conflict detection and priority-based resolution

Two pairs of tasks have overlapping time windows. `detect_conflicts` surfaces
both warnings; `handle_conflicts` then resolves each by keeping whichever task
claimed the slot first in priority order and dropping the one that conflicts.

```
=============================================
  CONFLICT DETECTION
=============================================
  WARNING: Morning Walk (Rex) 07:00–07:30  overlaps  Vet Call (Rex) 07:10–07:30
  WARNING: Brush Coat (Luna) 09:00–09:15  overlaps  Nail Trim (Luna) 09:10–09:20
```

**Morning Walk vs Vet Call** — both HIGH priority; Morning Walk wins because its
`preferred_time` (07:00) is earlier than Vet Call (07:10), so it sorts first and
claims the slot. Vet Call is dropped.

**Brush Coat vs Nail Trim** — both MEDIUM priority; Brush Coat (09:00) sorts
before Nail Trim (09:10) and claims the slot. Nail Trim is dropped.

The final schedule reflects these decisions: only the slot-winners appear.

### 3 — Recurring task auto-reschedule

Completing a recurring task stamps `last_done` and immediately queues a fresh
pending copy. The new copy is due the next day (`is_due` returns `False` for
today, `True` tomorrow).

```
=============================================
  RECURRING RESCHEDULE DEMO
=============================================
  Before:  Morning Walk  completed=False  last_done=None
  After:   Morning Walk  completed=True   last_done=2026-07-06
  Next:    Morning Walk  completed=False  last_done=2026-07-06
           is_due today    → False
           days_until_next → 1 day(s)
           next_due_date   → 2026-07-07
  Rex now has 5 tasks (new occurrence appended)
```

### 4 — Completion status filtering

```
=============================================
  PENDING TASKS
=============================================
  Flea Medication (Rex)
  Breakfast (Rex)
  Morning Walk (Rex)
  Vet Call (Rex)
  Feather Wand (Luna)
  Brush Coat (Luna)
  Nail Trim (Luna)

=============================================
  COMPLETED TASKS
=============================================
  Wet Food (Luna)
```

## 🖨️ Output Formatting

`main.py` uses two external libraries (`tabulate`, ANSI escape codes) plus several helper functions to produce color-coded, emoji-annotated CLI tables. `pawpal_system.py` remains unchanged and uses only Python builtins.

### `tabulate` — structured tables

**Library:** [`tabulate`](https://pypi.org/project/tabulate/) `>=0.9` (added to `requirements.txt`).

Every list section (schedule, priority sort, pending tasks, etc.) is rendered with `tabulate(..., tablefmt="rounded_outline")`, which draws rounded Unicode box-drawing borders:

```
╭────────┬────────────────┬────────┬────────────┬────────────╮
│ Time   │ Task           │ Pet    │ Priority   │ Duration   │
├────────┼────────────────┼────────┼────────────┼────────────┤
│ 07:00  │ 🦮 Morning Walk │ 🐕 Rex  │ ● HIGH     │ 30 min     │
╰────────┴────────────────┴────────┴────────────┴────────────╯
```

Each section builds a `rows` list of pre-formatted strings, then passes it to `tabulate` with explicit `headers`:

```python
# main.py — sorted-by-time table
rows = []
for t in scheduler.sort_by_time(all_tasks):
    pet = pet_map.get(id(t))
    rows.append([t.preferred_time or "—", fmt_task(t), fmt_pet(pet),
                 fmt_priority(t.priority), fmt_status(t.completed)])
print(tabulate(rows, headers=["Time", "Task", "Pet", "Priority", "Status"],
               tablefmt="rounded_outline"))
```

### ANSI color class `C` — `main.py`

Color is applied via ANSI escape sequences wrapped in a small helper class so color names are readable and the reset code is never forgotten:

```python
class C:
    RED     = "\033[91m"   # bright red  — HIGH priority, conflict warnings
    YELLOW  = "\033[93m"   # yellow      — MEDIUM priority, pending status
    GREEN   = "\033[92m"   # green       — LOW priority, done status
    CYAN    = "\033[96m"   # cyan        — section headers, weighted scores
    BOLD    = "\033[1m"    # bold        — section headers, HIGH label, time slots
    DIM     = "\033[2m"    # dim         — metadata lines, "before" labels
    RESET   = "\033[0m"    # reset all attributes
```

No third-party color library is needed — ANSI codes work in any modern terminal.

### Emoji dictionaries — `main.py`

Two module-level dicts map domain values to emoji so the mapping is defined once and reused everywhere:

```python
CATEGORY_EMOJI = {
    Category.WALK:       "🦮",
    Category.FEEDING:    "🍽️",
    Category.MEDS:       "💊",
    Category.ENRICHMENT: "🎾",
    Category.GROOMING:   "✂️",
}

SPECIES_EMOJI = {"dog": "🐕", "cat": "🐈", "other": "🐾"}
```

### Formatting helper functions — `main.py`

| Function | Returns | Purpose |
|----------|---------|---------|
| `fmt_priority(p)` | colored string | `● HIGH` in bold red, `◑ MED` in yellow, `○ LOW` in green |
| `fmt_status(completed)` | colored string | `✅ done` in green or `⏳ pending` in yellow |
| `fmt_task(task)` | string | category emoji + task name, e.g. `🦮 Morning Walk` |
| `fmt_pet(pet)` | string | species emoji + pet name, e.g. `🐕 Rex`; `"—"` when `None` |
| `section(title, icon)` | prints | bold cyan bar + icon + title as a section header |
| `display_plan(plan, title, icon)` | prints | full tabulate schedule table with budget line, skipped tasks, and explanation |

```python
def fmt_priority(p: Priority) -> str:
    if p == Priority.HIGH:
        return f"{C.RED}{C.BOLD}● HIGH{C.RESET}"
    if p == Priority.MEDIUM:
        return f"{C.YELLOW}◑ MED{C.RESET} "
    return f"{C.GREEN}○ LOW{C.RESET} "

def fmt_status(completed: bool) -> str:
    return f"{C.GREEN}✅ done{C.RESET}" if completed else f"{C.YELLOW}⏳ pending{C.RESET}"

def fmt_task(task: Task) -> str:
    return f"{CATEGORY_EMOJI.get(task.category, '📋')} {task.name}"

def fmt_pet(pet) -> str:
    if not pet:
        return "—"
    return f"{SPECIES_EMOJI.get(pet.species, '🐾')} {pet.name}"
```

### f-strings and format specs — `main.py` and `pawpal_system.py`

Python 3.6+ f-strings handle all inline interpolation throughout both files.

| Spec | Where | Effect |
|------|-------|--------|
| `:5.1f` | `main.py` — weighted score column | Right-aligns a float in a 5-character field with 1 decimal place so scores like `35.8` and `11.8` line up |
| `:02d` | `pawpal_system.py` — `assign_times`, `detect_conflicts` | Zero-pads an integer to 2 digits so clock times render as `07:00` not `7:0` |

```python
# main.py — float score column
f"{C.CYAN}{t.weighted_score(TODAY):5.1f}{C.RESET}"

# pawpal_system.py — Scheduler.assign_times()
slot = f"{cursor // 60:02d}:{cursor % 60:02d}"
```

### `str.join()` — `pawpal_system.py`

`Plan.display()` and `Task.__str__()` accumulate parts in a list and join at the end rather than concatenating in a loop.

```python
# Task.__str__() — pawpal_system.py
parts = [self.name, f"[{self.category.value}]", ...]
return " | ".join(parts)
```

### Summary table

| Feature | Implementation | Defined in |
|---------|---------------|------------|
| Structured tables | `tabulate(..., tablefmt="rounded_outline")` | `main.py` |
| Color-coded priority | `fmt_priority()` via ANSI `C` class | `main.py` |
| Color-coded status | `fmt_status()` via ANSI `C` class | `main.py` |
| Category emojis | `CATEGORY_EMOJI` dict + `fmt_task()` | `main.py` |
| Species emojis | `SPECIES_EMOJI` dict + `fmt_pet()` | `main.py` |
| Section headers | `section()` — bold cyan bar + icon | `main.py` |
| Schedule display | `display_plan()` — wraps tabulate + budget line | `main.py` |
| Fixed-width float | `{value:5.1f}` | `main.py` (weighted score column) |
| Zero-padded integer | `{value:02d}` | `pawpal_system.py` (`assign_times`, `detect_conflicts`) |
| Multi-line assembly | `"\n".join(lines)` | `pawpal_system.py` (`Plan.display`) |
| None fallback | `value or "—"` | `main.py` |

## 🧪 Testing PawPal+

### How to run

```bash
python3 -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| Area | Tests | What is verified |
|---|---|---|
| **Task lifecycle** | 3 | `mark_complete` sets the flag and is idempotent; adding tasks grows the pet's list |
| **Sorting** | 3 | `sort_by_time` returns earliest-first; untimed tasks sort last; `sort_by_priority` returns HIGH → MEDIUM → LOW |
| **Recurrence** | 5 | Completing a daily task queues a fresh pending copy; daily/weekly `is_due` boundaries including the exact-7-day edge case; non-recurring tasks return `None` and do not mutate the list |
| **Conflict detection** | 4 | Overlapping windows produce a warning; back-to-back (shared endpoint) does not; `handle_conflicts` keeps the higher-priority task and drops the lower |

### Test run output

```
============================= test session starts ==============================
platform darwin -- Python 3.14.5, pytest-9.0.3, pluggy-1.6.0 -- /Library/Frameworks/Python.framework/Versions/3.14/bin/python3
cachedir: .pytest_cache
rootdir: /Users/valeria./Documents/codepath/AI201/week4/ai110-module2show-pawpal-starter
plugins: anyio-4.13.0
collecting ... collected 16 items

tests/test_pawpal.py::test_mark_complete_sets_completed_true PASSED      [  6%]
tests/test_pawpal.py::test_mark_complete_is_idempotent PASSED            [ 12%]
tests/test_pawpal.py::test_add_task_increases_pet_task_count PASSED      [ 18%]
tests/test_pawpal.py::test_sort_by_time_returns_chronological_order PASSED [ 25%]
tests/test_pawpal.py::test_sort_by_time_tasks_without_preferred_time_sort_last PASSED [ 31%]
tests/test_pawpal.py::test_sort_by_priority_highest_first PASSED         [ 37%]
tests/test_pawpal.py::test_complete_daily_task_queues_next_occurrence PASSED [ 43%]
tests/test_pawpal.py::test_daily_task_done_today_is_not_due PASSED       [ 50%]
tests/test_pawpal.py::test_daily_task_done_yesterday_is_due PASSED       [ 56%]
tests/test_pawpal.py::test_weekly_task_exactly_seven_days_ago_is_due PASSED [ 62%]
tests/test_pawpal.py::test_weekly_task_done_three_days_ago_is_not_due PASSED [ 68%]
tests/test_pawpal.py::test_non_recurring_task_complete_does_not_queue_next PASSED [ 75%]
tests/test_pawpal.py::test_detect_conflicts_flags_overlapping_tasks PASSED [ 81%]
tests/test_pawpal.py::test_detect_conflicts_no_warning_for_back_to_back_tasks PASSED [ 87%]
tests/test_pawpal.py::test_detect_conflicts_no_warning_for_non_overlapping_tasks PASSED [ 93%]
tests/test_pawpal.py::test_handle_conflicts_keeps_higher_priority_task PASSED [100%]

============================== 16 passed in 0.02s ==============================
```

### Confidence Level: ★★★★☆ (4 / 5)

The core scheduling behaviors — priority sorting, recurrence windows, and conflict resolution — all pass, including the tricky boundary cases (exact 7-day weekly window, back-to-back tasks). The missing star reflects two gaps: `generate_plan` end-to-end is not tested as a full integration (pet-map wiring, budget overflow warning, multi-pet scheduling), and there is no test for a pet or owner with zero tasks to confirm the system handles empty states without crashing.

## ✅ Features

### Sorting
- **Priority-based sorting** (`Scheduler.sort_by_priority`) — orders tasks HIGH → MEDIUM → LOW using the `Priority` enum's numeric value. Ties at the same priority level are broken by `preferred_time` ascending, so the earlier task wins a slot conflict.
- **Chronological sorting** (`Scheduler.sort_by_time`) — orders tasks by `preferred_time`, converting `"HH:MM"` to total minutes for a numeric (not lexicographic) comparison. Tasks with no `preferred_time` receive a sentinel of `9999` and sort to the end of the list.

### Filtering
- **Start-time filtering** (`Scheduler.filter_by_time`) — drops any task whose `preferred_time` falls before the scheduler's `start_time`. Tasks with no `preferred_time` always pass through.
- **Completion-status filtering** (`Scheduler.filter_by_status`) — returns only pending tasks by default (`completed=False`); pass `completed=True` to retrieve finished tasks instead.
- **Per-pet filtering** (`Scheduler.filter_by_pet`) — isolates tasks belonging to one named pet using a `pet_map` (`id(task) → Pet`) built from `Owner.all_tasks()`.
- **Recurrence filtering** (`Scheduler.filter_by_recurrence`) — drops recurring tasks already completed within their cadence window by delegating to `Task.is_due(today)` for each task. Non-recurring tasks always pass through.

### Recurrence
- **Daily recurrence** (`Task.is_due`) — a daily task is considered due unless `last_done == today`.
- **Weekly recurrence** (`Task.is_due`) — a weekly task is considered due once at least 7 days have elapsed since `last_done` (exact boundary: `>= 7` days).
- **Next-occurrence auto-queuing** (`Pet.complete_task`) — on completion of a recurring task, stamps `last_done`, then appends and returns a fresh pending copy via `Task.next_occurrence()` (`dataclasses.replace` with `completed=False`).
- **Next due date** (`Task.next_due_date`) — computes the calendar date string when the task is next due: `last_done + 1 day` for daily, `last_done + 7 days` for weekly.
- **Days until next** (`Task.days_until_next`) — returns how many days remain before the cadence window reopens; `0` means due today, `-1` means non-recurring.

### Conflict Detection & Resolution
- **Conflict detection** (`Scheduler.detect_conflicts`) — O(n²) pairwise scan over tasks that have a `preferred_time`. Each pair is checked exactly once. Overlap condition: `a_start < b_end and b_start < a_end`. Back-to-back tasks (shared endpoint) do not trigger a warning. Returns warning strings; does not modify the task list.
- **Conflict resolution** (`Scheduler.handle_conflicts`) — processes tasks in priority order (highest first); a task is dropped when its time window overlaps an already-claimed slot. The first (highest-priority) claimant always wins.

### Plan Generation
- **Time-slot assignment** (`Scheduler.assign_times`) — walks tasks in order and assigns a clock time to each. If a task's `preferred_time` is at or after the current cursor, the cursor snaps forward to it; otherwise the task inherits the cursor position. The cursor advances by `task.duration` after each assignment.
- **Budget-aware scheduling** (`Scheduler.generate_plan`) — fits tasks within `available_minutes`; tasks that cannot fit are recorded as skipped with `"insufficient time remaining"`. Emits an overflow warning when total requested time exceeds the budget.
- **Multi-pet plan** (`Scheduler.generate_plan` with `pet_map`) — handles tasks across multiple pets in a single plan pass. Each scheduled row is annotated with the owning pet via the `id(task) → Pet` mapping.
- **Full scheduling pipeline** — `generate_plan` orchestrates a fixed six-stage pipeline: `sort_by_priority` → `filter_by_time` → `filter_by_status` → `filter_by_recurrence` → `handle_conflicts` → `assign_times`, then applies the time budget.

## 📐 Smarter Scheduling

### Sorting

| Method | Behavior |
|--------|----------|
| `Scheduler.sort_by_priority()` | Sorts HIGH → MEDIUM → LOW using `Priority` enum values. Ties within the same priority are broken by `preferred_time` ascending so earlier tasks win conflicts. |
| `Scheduler.sort_by_time()` | Sorts tasks chronologically by `preferred_time`. Converts `"HH:MM"` to total minutes for numeric comparison. Tasks without a `preferred_time` receive a sentinel of `9999` and sort to the end. |

### Filtering

| Method | Behavior |
|--------|----------|
| `Scheduler.filter_by_time()` | Drops tasks whose `preferred_time` falls before the scheduler's `start_time`. Tasks with no `preferred_time` always pass through. |
| `Scheduler.filter_by_status()` | Returns tasks matching a given completion state. Defaults to pending-only (`completed=False`); pass `completed=True` to retrieve finished tasks. |
| `Scheduler.filter_by_pet()` | Returns only tasks belonging to a named pet, using the `pet_map` (id(task) → Pet) built from `Owner.all_tasks()`. |
| `Scheduler.filter_by_recurrence()` | Drops recurring tasks already completed within their cadence window. Delegates to `Task.is_due(today)` for each task. Non-recurring tasks always pass through. |

### Conflict Detection

| Method | Behavior |
|--------|----------|
| `Scheduler.detect_conflicts()` | Scans all task pairs whose `preferred_time` windows overlap (O(n²), each pair checked once). Returns a list of warning strings — does not modify the schedule or raise exceptions. |
| `Scheduler.handle_conflicts()` | Resolves conflicts by keeping the higher-priority task and dropping lower-priority tasks that overlap an already-claimed slot. Tasks are processed in priority order so the first claim always wins. |

### Recurring Task Logic

| Method | Behavior |
|--------|----------|
| `Task.is_due(today)` | Returns `False` only when a recurring task was completed within its window: same day for `"daily"`, within 7 days for `"weekly"`. |
| `Task.mark_complete(today)` | Sets `completed=True` and stamps `last_done` with today's date for recurring tasks. |
| `Task.next_occurrence()` | Returns a fresh copy of the task with `completed=False` via `dataclasses.replace`. `last_done` is preserved so `is_due()` knows the window start. |
| `Pet.complete_task(task, today)` | Marks a task complete and, if recurring, appends and returns the next occurrence to the pet's task list automatically. |
| `Task.next_due_date()` | Returns the calendar date (`"YYYY-MM-DD"`) when the task is next due, computed as `last_done + timedelta(days=1)` for daily or `+ timedelta(days=7)` for weekly. |
| `Task.days_until_next(today)` | Returns the number of days remaining until the task window reopens. Returns `0` if due today, `-1` if non-recurring. |

## 📸 Demo Walkthrough

1. Run `python3 main.py` in the terminal from the project root.
2. The script creates owner **Valeria** with 120 available minutes and two pets: **Rex** (Labrador) and **Luna** (Siamese).
3. Each pet has three tasks with different priorities and preferred times (e.g. Morning Walk at 07:00, Breakfast at 07:30).
4. The `Scheduler` sorts all tasks by priority (HIGH first), resolves time conflicts, and assigns sequential time slots starting at 07:00.
5. The final plan prints as a single "Today's Schedule" section — each task row shows the pet name, priority, assigned time, and duration.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

---

## 💾 Persistence

### Files modified

| File | Change |
|------|--------|
| `pawpal_system.py` | Added `import json` at the top; added `Owner.save_to_json()` and `Owner.load_from_json()` methods |

No other files were changed. The rest of the system (`app.py`, `main.py`, tests) is unaffected.

### How it works

On the **first run** the app creates pets and tasks in memory as usual.
Before the app exits (or whenever the user clicks "Save"), call:

```python
owner.save_to_json("data.json")
```

On **every subsequent run**, load the saved state before building the UI:

```python
import os
if os.path.exists("data.json"):
    owner = Owner.load_from_json("data.json")
else:
    owner = Owner(name="...", available_minutes=120)
```

The full object graph — owner → pets → tasks, including all enum values, recurrence state, and `last_done` dates — is round-tripped through `data.json`.

### JSON format

```json
{
  "name": "Valeria",
  "available_minutes": 120,
  "preferences": null,
  "pets": [
    {
      "name": "Rex",
      "species": "dog",
      "breed": "Labrador",
      "tasks": [
        {
          "name": "Morning Walk",
          "category": "walk",
          "duration": 30,
          "priority": 3,
          "preferred_time": "07:00",
          "recurring": "daily",
          "completed": false,
          "last_done": null
        }
      ]
    }
  ]
}
```

`category` is stored as its string value (`"walk"`, `"meds"`, …) and `priority` as its integer value (`1`=LOW, `2`=MEDIUM, `3`=HIGH) so the file is human-readable and easy to hand-edit.

---

## 🔄 Serialization approaches

The built-in approach used here is a plain custom dict conversion. Two alternatives worth knowing:

### Option A — Custom dict conversion (current approach)

`save_to_json` manually builds a nested dict, converting enums to primitives.
`load_from_json` reverses that with `Category(value)` / `Priority(value)`.

**Pros:** zero extra dependencies; completely transparent; easy to debug.  
**Cons:** every new field must be added to both methods by hand.

```python
# serialize
{"category": task.category.value, "priority": task.priority.value, ...}

# deserialize
Task(category=Category(d["category"]), priority=Priority(d["priority"]), ...)
```

### Option B — marshmallow

[marshmallow](https://marshmallow.readthedocs.io/) defines a `Schema` class per model.
Fields, validation rules, and enum handling all live in one place.

```bash
pip install marshmallow marshmallow-enum
```

```python
from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField

class TaskSchema(Schema):
    name          = fields.Str()
    category      = EnumField(Category, by_value=True)
    duration      = fields.Int()
    priority      = EnumField(Priority, by_value=True)
    preferred_time = fields.Str(load_default=None)
    recurring     = fields.Str(load_default=None)
    completed     = fields.Bool(load_default=False)
    last_done     = fields.Str(load_default=None)

    @post_load
    def make_task(self, data, **kwargs):
        return Task(**data)

class PetSchema(Schema):
    name    = fields.Str()
    species = fields.Str()
    breed   = fields.Str(load_default=None)
    tasks   = fields.List(fields.Nested(TaskSchema))

    @post_load
    def make_pet(self, data, **kwargs):
        pet = Pet(name=data["name"], species=data["species"], breed=data["breed"])
        for task in data["tasks"]:
            pet.add_task(task)
        return pet

# save
json.dump(PetSchema(many=True).dump(owner.pets), f)

# load
pets = PetSchema(many=True).load(data["pets"])
```

**Pros:** automatic validation; adding a field only requires one schema change; nested schemas compose cleanly.  
**Cons:** extra dependency; more boilerplate upfront; `marshmallow-enum` is a third-party add-on.

### Option C — dataclasses + `dacite`

[dacite](https://github.com/konradhalas/dacite) reconstructs dataclasses from dicts automatically, handling type coercion with a `Config`.

```bash
pip install dacite
```

```python
import dacite

# save (enums → primitives, same as Option A)
task_dict = {**vars(task), "category": task.category.value, "priority": task.priority.value}

# load — dacite resolves Union, Optional, and nested dataclasses for you
task = dacite.from_dict(Task, task_dict, config=dacite.Config(cast=[Enum]))
```

**Pros:** almost no boilerplate; works well with existing `@dataclass` definitions.  
**Cons:** another dependency; less control over field-level validation than marshmallow.
