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
Total scheduled time: 85 min

Scheduled:
  [HIGH] Morning Walk (Rex) @ 07:00 (30 min)
  [HIGH] Breakfast (Rex) @ 07:30 (10 min)
  [HIGH] Wet Food (Luna) @ 07:40 (5 min)
  [MEDIUM] Flea Medication (Rex) @ 07:45 (5 min)
  [MEDIUM] Brush Coat (Luna) @ 07:50 (15 min)
  [LOW] Feather Wand (Luna) @ 08:05 (20 min)

Scheduled 6 task(s) using 85/120 available minutes.
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

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
