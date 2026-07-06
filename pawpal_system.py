from __future__ import annotations
from dataclasses import dataclass, field, replace
from datetime import date as _date, timedelta
from enum import Enum
from typing import Optional


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Category(Enum):
    WALK = "walk"
    FEEDING = "feeding"
    MEDS = "meds"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"


@dataclass
class Task:
    name: str
    category: Category
    duration: int  # minutes
    priority: Priority
    preferred_time: Optional[str] = None  # e.g. "08:00"
    recurring: Optional[str] = None  # e.g. "daily" or "weekly"
    completed: bool = False
    last_done: Optional[str] = None  # "YYYY-MM-DD" for recurring tasks

    def mark_complete(self, today: Optional[str] = None) -> None:
        """Mark this task as completed and record the date for recurring tasks."""
        self.completed = True
        if self.recurring:
            self.last_done = today or str(_date.today())

    def next_occurrence(self) -> "Task":
        """Return a fresh copy of this recurring task reset for its next run.

        Copies all fields via dataclasses.replace, overriding only completed=False.
        last_done is preserved so is_due() knows when the task was last performed.
        Only meaningful when recurring is set; calling on a non-recurring task still
        returns a copy but the result won't be filtered by filter_by_recurrence.
        """
        return replace(self, completed=False)

    def is_due(self, today: str) -> bool:
        """Return True if this task should appear in today's schedule.

        Args:
            today: date string in "YYYY-MM-DD" format.

        Returns True when:
          - the task has no recurring cadence, or
          - last_done is None (never been done), or
          - daily: last_done is not today, or
          - weekly: at least 7 days have elapsed since last_done.
        Returns False only when the task was already completed within its window.
        """
        if not self.recurring or not self.last_done:
            return True
        if self.recurring == "daily":
            return self.last_done != today
        if self.recurring == "weekly":
            return (_date.fromisoformat(today) - _date.fromisoformat(self.last_done)).days >= 7
        return True

    def next_due_date(self) -> Optional[str]:
        """Return the calendar date when this task is next due.

        Uses timedelta to add the cadence interval to last_done:
          daily  → last_done + 1 day
          weekly → last_done + 7 days

        Returns a "YYYY-MM-DD" string, or None if the task is non-recurring
        or has never been completed (last_done is None).
        """
        if not self.recurring or not self.last_done:
            return None
        base = _date.fromisoformat(self.last_done)
        if self.recurring == "daily":
            return str(base + timedelta(days=1))
        if self.recurring == "weekly":
            return str(base + timedelta(days=7))
        return None

    def days_until_next(self, today: str) -> int:
        """Return how many days remain until this task is due again.

        Args:
            today: date string in "YYYY-MM-DD" format.

        Returns:
             0  — due today (never done, or window already elapsed).
            -1  — task is non-recurring; concept of "next" doesn't apply.
            >0  — days remaining before the cadence window reopens.

        Example: a daily task completed today returns 1; a weekly task
        completed 3 days ago returns 4.
        """
        if not self.recurring:
            return -1
        if not self.last_done:
            return 0
        elapsed = (_date.fromisoformat(today) - _date.fromisoformat(self.last_done)).days
        if self.recurring == "daily":
            return max(0, 1 - elapsed)
        if self.recurring == "weekly":
            return max(0, 7 - elapsed)
        return 0

    def priority_value(self) -> int:
        """Return the numeric value of this task's priority."""
        return self.priority.value

    def __str__(self) -> str:
        status = "DONE" if self.completed else "pending"
        parts = [
            f"{self.name}",
            f"[{self.category.value}]",
            f"{self.priority.name} priority",
            f"{self.duration} min",
            status,
        ]
        if self.preferred_time:
            parts.append(f"@ {self.preferred_time}")
        if self.recurring:
            recur = f"({self.recurring}"
            if self.last_done:
                recur += f", last done {self.last_done}"
            recur += ")"
            parts.append(recur)
        return " | ".join(parts)


@dataclass
class Pet:
    name: str
    species: str
    breed: Optional[str] = None
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet's task list."""
        self.tasks.remove(task)

    def edit_task(self, task: Task, **changes) -> None:
        """Update one or more fields on an existing task."""
        if task in self.tasks:
            for attr, value in changes.items():
                setattr(task, attr, value)

    def complete_task(self, task: Task, today: Optional[str] = None) -> Optional[Task]:
        """Mark a task complete and automatically queue the next occurrence if recurring.

        Args:
            task:  a Task already in this pet's task list.
            today: date string "YYYY-MM-DD" stamped onto last_done. Defaults to today.

        Returns the new Task instance appended to self.tasks when recurring is set,
        or None for non-recurring tasks. The original task is mutated in place
        (completed=True, last_done set).
        """
        task.mark_complete(today)
        if task.recurring:
            next_task = task.next_occurrence()
            self.tasks.append(next_task)
            return next_task
        return None

    def list_tasks(self) -> list[Task]:
        """Return a copy of this pet's task list."""
        return list(self.tasks)


class Owner:
    def __init__(
        self,
        name: str,
        available_minutes: int,
        preferences: Optional[str] = None,
    ) -> None:
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pet list."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner's pet list."""
        self.pets.remove(pet)

    def get_pet(self, name: str) -> Optional[Pet]:
        """Return the pet with the given name, or None if not found."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        return None

    def all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all (pet, task) pairs across every pet this owner has."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def tasks_for_pet(self, name: str) -> list[tuple[Pet, Task]]:
        """Return all (pet, task) pairs for the named pet, or [] if not found."""
        pet = self.get_pet(name)
        return [(pet, task) for task in pet.tasks] if pet else []

    def pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Return only (pet, task) pairs where the task is not yet completed."""
        return [(pet, task) for pet, task in self.all_tasks() if not task.completed]


class Plan:
    def __init__(self, owner: "Owner", pet: Optional["Pet"] = None) -> None:
        self.owner = owner
        self.pet = pet
        self.scheduled_tasks: list[tuple[Task, Optional[str], Optional["Pet"]]] = []
        self.skipped_tasks: list[tuple[Task, str]] = []
        self.explanation: str = ""
        self.total_minutes: int = 0

    def add_scheduled(self, task: Task, time: Optional[str] = None, pet: Optional["Pet"] = None) -> None:
        """Record a task as scheduled and add its duration to the total."""
        self.scheduled_tasks.append((task, time, pet))
        self.total_minutes += task.duration

    def add_skipped(self, task: Task, reason: str) -> None:
        """Record a task as skipped with an explanation."""
        self.skipped_tasks.append((task, reason))

    def display(self) -> str:
        """Format the plan as a human-readable string."""
        lines = [f"=== Care Plan for {self.owner.name} ==="]
        lines.append(f"Total scheduled time: {self.total_minutes} min\n")

        lines.append("Scheduled:")
        if self.scheduled_tasks:
            for task, time_slot, pet in self.scheduled_tasks:
                slot = f" @ {time_slot}" if time_slot else ""
                pet_label = f" ({pet.name})" if pet else ""
                lines.append(f"  [{task.priority.name}] {task.name}{pet_label}{slot} ({task.duration} min)")
        else:
            lines.append("  (none)")

        if self.skipped_tasks:
            lines.append("\nSkipped:")
            for task, reason in self.skipped_tasks:
                lines.append(f"  {task.name} — {reason}")

        if self.explanation:
            lines.append(f"\n{self.explanation}")

        return "\n".join(lines)


class Scheduler:
    def __init__(self, owner: "Owner", start_time: Optional[str] = None) -> None:
        self.owner = owner
        self.available_minutes = owner.available_minutes
        self.start_time = start_time

    def generate_plan(
        self,
        tasks: list[Task],
        pet: Optional["Pet"] = None,
        pet_map: Optional[dict[int, "Pet"]] = None,
        today: Optional[str] = None,
    ) -> Plan:
        """Build a time-ordered Plan by sorting, filtering, and assigning tasks."""
        today = today or str(_date.today())
        plan = Plan(self.owner, pet)

        sorted_tasks = self.sort_by_priority(tasks)
        filtered_tasks = self.filter_by_time(sorted_tasks)
        active_tasks = self.filter_by_status(filtered_tasks)
        due_tasks = self.filter_by_recurrence(active_tasks, today)
        resolved_tasks = self.handle_conflicts(due_tasks)
        timed_tasks = self.assign_times(resolved_tasks)

        total_requested = sum(t.duration for t in due_tasks)
        warning = (
            f"Warning: {total_requested} min requested, only "
            f"{self.available_minutes} min available — some tasks will be skipped.\n"
            if total_requested > self.available_minutes else ""
        )

        remaining = self.available_minutes
        for task, time_slot in timed_tasks:
            if task.duration <= remaining:
                task_pet = pet_map.get(id(task)) if pet_map else pet
                plan.add_scheduled(task, time_slot, task_pet)
                remaining -= task.duration
            else:
                plan.add_skipped(task, "insufficient time remaining")

        scheduled_count = len(plan.scheduled_tasks)
        plan.explanation = (
            f"{warning}Scheduled {scheduled_count} task(s) using "
            f"{plan.total_minutes}/{self.available_minutes} available minutes."
        )
        return plan

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks highest-priority first; break ties by preferred_time."""
        return sorted(tasks, key=lambda t: (-t.priority_value(), t.preferred_time or "99:99"))

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks chronologically by preferred_time.

        Converts "HH:MM" to total minutes for numeric comparison so the sort
        is not sensitive to zero-padding. Tasks without a preferred_time receive
        a sentinel value of 9999 minutes and sort to the end of the list.
        """
        return sorted(tasks, key=lambda t: (
            int(t.preferred_time[:2]) * 60 + int(t.preferred_time[3:])
            if t.preferred_time else 9999
        ))

    def filter_by_time(self, tasks: list[Task]) -> list[Task]:
        """Drop tasks whose preferred_time falls before the scheduler's start time."""
        if not self.start_time:
            return tasks

        sh, sm = map(int, self.start_time.split(":"))
        start_min = sh * 60 + sm

        result = []
        for task in tasks:
            if task.preferred_time is None:
                result.append(task)
            else:
                th, tm = map(int, task.preferred_time.split(":"))
                if th * 60 + tm >= start_min:
                    result.append(task)
        return result

    def filter_by_status(self, tasks: list[Task], completed: bool = False) -> list[Task]:
        """Return only tasks matching the given completion status.

        Args:
            tasks:     list of Task objects to filter.
            completed: if False (default), returns pending tasks only;
                       if True, returns completed tasks only.
        """
        return [t for t in tasks if t.completed == completed]

    def filter_by_pet(
        self,
        tasks: list[Task],
        pet_name: str,
        pet_map: dict[int, "Pet"],
    ) -> list[Task]:
        """Return only tasks belonging to the named pet.

        Args:
            tasks:    flat list of Task objects to filter.
            pet_name: name of the pet to isolate (case-sensitive).
            pet_map:  mapping of id(task) → Pet, built from owner.all_tasks().

        Tasks not present in pet_map (e.g. dynamically appended after pet_map
        was constructed) will be excluded from the result.
        """
        return [t for t in tasks if pet_map.get(id(t)) and pet_map[id(t)].name == pet_name]

    def filter_by_recurrence(self, tasks: list[Task], today: str) -> list[Task]:
        """Drop recurring tasks already completed within their cadence window.

        Delegates to Task.is_due(today) for each task. Non-recurring tasks
        always pass through. Recurring tasks with no last_done also pass through
        (they have never been done).

        Args:
            today: date string "YYYY-MM-DD" used to evaluate each task's window.
        """
        return [t for t in tasks if t.is_due(today)]

    def assign_times(self, tasks: list[Task]) -> list[tuple[Task, Optional[str]]]:
        """Pair each task with a clock time, snapping to preferred_time when available."""
        if not self.start_time:
            return [(task, None) for task in tasks]

        h, m = map(int, self.start_time.split(":"))
        cursor = h * 60 + m
        result = []
        for task in tasks:
            if task.preferred_time:
                th, tm = map(int, task.preferred_time.split(":"))
                preferred = th * 60 + tm
                if preferred >= cursor:
                    cursor = preferred
            slot = f"{cursor // 60:02d}:{cursor % 60:02d}"
            result.append((task, slot))
            cursor += task.duration
        return result

    def detect_conflicts(
        self,
        tasks: list[Task],
        pet_map: Optional[dict[int, "Pet"]] = None,
    ) -> list[str]:
        """Return a warning string for every pair of tasks whose time windows overlap.

        Uses an O(n²) pairwise check over tasks that have a preferred_time.
        Each pair (a, b) is checked exactly once (inner loop starts at i+1).
        Overlap condition: a_start < b_end and b_start < a_end.

        Args:
            tasks:   flat list of Task objects to scan.
            pet_map: optional id(task) → Pet mapping for labelling warnings.

        Returns an empty list if no conflicts are found. Does not modify the
        task list or raise exceptions — callers decide how to handle warnings.
        """
        warnings = []
        timed = [t for t in tasks if t.preferred_time]

        for i, a in enumerate(timed):
            ah, am = map(int, a.preferred_time.split(":"))
            a_start = ah * 60 + am
            a_end = a_start + a.duration

            for b in timed[i + 1:]:
                bh, bm = map(int, b.preferred_time.split(":"))
                b_start = bh * 60 + bm
                b_end = b_start + b.duration

                no_overlap = (a_end <= b_start) or (b_end <= a_start)
                if not no_overlap:
                    a_pet = pet_map[id(a)].name if pet_map and pet_map.get(id(a)) else "?"
                    b_pet = pet_map[id(b)].name if pet_map and pet_map.get(id(b)) else "?"
                    warnings.append(
                        f"  WARNING: {a.name} ({a_pet}) {a.preferred_time}–"
                        f"{a_end // 60:02d}:{a_end % 60:02d}"
                        f"  overlaps  "
                        f"{b.name} ({b_pet}) {b.preferred_time}–"
                        f"{b_end // 60:02d}:{b_end % 60:02d}"
                    )
        return warnings

    def handle_conflicts(self, tasks: list[Task]) -> list[Task]:
        """Remove lower-priority tasks whose time window overlaps an already-claimed slot."""
        # Tasks are already sorted by priority (highest first).
        # A task with a preferred_time conflicts if its window overlaps an already-claimed slot.
        occupied: list[tuple[int, int]] = []  # (start_min, end_min)
        result = []

        for task in tasks:
            if task.preferred_time is None:
                result.append(task)
                continue

            h, m = map(int, task.preferred_time.split(":"))
            start = h * 60 + m
            end = start + task.duration

            overlaps = any(not (end <= s or start >= e) for s, e in occupied)
            if not overlaps:
                occupied.append((start, end))
                result.append(task)

        return result
