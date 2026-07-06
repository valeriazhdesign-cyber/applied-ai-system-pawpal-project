from datetime import date
from tabulate import tabulate
from pawpal_system import Category, Owner, Pet, Priority, Scheduler, Task

TODAY = str(date.today())

# ── ANSI color helpers ─────────────────────────────────────────────────────────
class C:
    RED     = "\033[91m"
    YELLOW  = "\033[93m"
    GREEN   = "\033[92m"
    CYAN    = "\033[96m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"

CATEGORY_EMOJI = {
    Category.WALK:       "🦮",
    Category.FEEDING:    "🍽️",
    Category.MEDS:       "💊",
    Category.ENRICHMENT: "🎾",
    Category.GROOMING:   "✂️",
}

SPECIES_EMOJI = {"dog": "🐕", "cat": "🐈", "other": "🐾"}

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

def section(title: str, icon: str = "▸") -> None:
    bar = "─" * 54
    print(f"\n{C.BOLD}{C.CYAN}{bar}")
    print(f"  {icon}  {title}")
    print(f"{bar}{C.RESET}")

def display_plan(plan, title: str = "TODAY'S SCHEDULE", icon: str = "📅") -> None:
    section(title, icon)
    print(f"  {C.DIM}Owner: {plan.owner.name}  |  Budget: {plan.owner.available_minutes} min{C.RESET}\n")
    if plan.scheduled_tasks:
        rows = []
        for task, time_slot, pet in plan.scheduled_tasks:
            rows.append([
                f"{C.BOLD}{time_slot or '—'}{C.RESET}",
                fmt_task(task),
                fmt_pet(pet),
                fmt_priority(task.priority),
                f"{task.duration} min",
            ])
        print(tabulate(rows,
                       headers=["Time", "Task", "Pet", "Priority", "Duration"],
                       tablefmt="rounded_outline"))
    else:
        print(f"  {C.DIM}(no tasks scheduled){C.RESET}")

    if plan.skipped_tasks:
        print(f"\n  {C.RED}{C.BOLD}Skipped:{C.RESET}")
        for task, reason in plan.skipped_tasks:
            print(f"    {C.RED}✗{C.RESET} {fmt_task(task)}  {C.DIM}— {reason}{C.RESET}")

    print(f"\n  {C.DIM}{plan.explanation}{C.RESET}")


# ── Owner ──────────────────────────────────────────────────────────────────────
owner = Owner("Valeria", available_minutes=120, preferences="morning routine")

# ── Pets ───────────────────────────────────────────────────────────────────────
rex  = Pet("Rex",  species="dog", breed="Labrador")
luna = Pet("Luna", species="cat", breed="Siamese")

owner.add_pet(rex)
owner.add_pet(luna)

# Tasks added OUT OF ORDER intentionally to demonstrate sorting
rex.add_task(Task("Flea Medication", Category.MEDS,       duration=5,  priority=Priority.MEDIUM, preferred_time="08:00", recurring="weekly", last_done="2026-07-05"))
rex.add_task(Task("Breakfast",       Category.FEEDING,    duration=10, priority=Priority.HIGH,   preferred_time="07:30"))
rex.add_task(Task("Morning Walk",    Category.WALK,       duration=30, priority=Priority.HIGH,   preferred_time="07:00", recurring="daily"))
# Conflicts with Morning Walk (07:00–07:30)
rex.add_task(Task("Vet Call",        Category.MEDS,       duration=20, priority=Priority.HIGH,   preferred_time="07:10"))

luna.add_task(Task("Feather Wand",   Category.ENRICHMENT, duration=20, priority=Priority.LOW,    preferred_time="09:30"))
luna.add_task(Task("Brush Coat",     Category.GROOMING,   duration=15, priority=Priority.MEDIUM, preferred_time="09:00", recurring="weekly"))
luna.add_task(Task("Wet Food",       Category.FEEDING,    duration=5,  priority=Priority.HIGH,   preferred_time="08:15"))
# Conflicts with Brush Coat (09:00–09:15)
luna.add_task(Task("Nail Trim",      Category.GROOMING,   duration=10, priority=Priority.MEDIUM, preferred_time="09:10"))

# Simulate: Wet Food already given this morning (non-recurring, so no next occurrence)
luna.complete_task(luna.tasks[2], TODAY)

# ── Shared setup ───────────────────────────────────────────────────────────────
scheduler     = Scheduler(owner, start_time="07:00")
all_pet_tasks = owner.all_tasks()
pet_map       = {id(task): pet for pet, task in all_pet_tasks}
all_tasks     = [task for _, task in all_pet_tasks]

# ── Today's schedule ───────────────────────────────────────────────────────────
plan = scheduler.generate_plan(all_tasks, pet_map=pet_map, today=TODAY)
display_plan(plan, "TODAY'S SCHEDULE", "📅")

# ── Conflict detection ─────────────────────────────────────────────────────────
section("CONFLICT DETECTION", "⚠️")
conflict_warnings = scheduler.detect_conflicts(all_tasks, pet_map)
if conflict_warnings:
    for w in conflict_warnings:
        print(f"  {C.RED}{C.BOLD}⚠  {w.strip()}{C.RESET}")
else:
    print(f"  {C.GREEN}✔  No conflicts detected.{C.RESET}")

# ── Sorted by time ─────────────────────────────────────────────────────────────
section("SORTED BY TIME", "🕐")
rows = []
for t in scheduler.sort_by_time(all_tasks):
    pet = pet_map.get(id(t))
    rows.append([
        t.preferred_time or "—",
        fmt_task(t),
        fmt_pet(pet),
        fmt_priority(t.priority),
        fmt_status(t.completed),
    ])
print(tabulate(rows, headers=["Time", "Task", "Pet", "Priority", "Status"],
               tablefmt="rounded_outline"))

# ── Sorted by priority ─────────────────────────────────────────────────────────
section("SORTED BY PRIORITY", "🔺")
rows = []
for t in scheduler.sort_by_priority(all_tasks):
    pet = pet_map.get(id(t))
    rows.append([
        fmt_priority(t.priority),
        fmt_task(t),
        fmt_pet(pet),
        f"{t.duration} min",
        fmt_status(t.completed),
    ])
print(tabulate(rows, headers=["Priority", "Task", "Pet", "Duration", "Status"],
               tablefmt="rounded_outline"))

# ── Sorted by weighted priority ────────────────────────────────────────────────
section("SORTED BY WEIGHTED PRIORITY", "⚡")
rows = []
for t in scheduler.sort_by_weighted_priority(all_tasks, TODAY):
    pet = pet_map.get(id(t))
    rows.append([
        f"{C.CYAN}{t.weighted_score(TODAY):5.1f}{C.RESET}",
        fmt_priority(t.priority),
        fmt_task(t),
        fmt_pet(pet),
        fmt_status(t.completed),
    ])
print(tabulate(rows, headers=["Score", "Priority", "Task", "Pet", "Status"],
               tablefmt="rounded_outline"))

# ── Weighted schedule ──────────────────────────────────────────────────────────
weighted_plan = scheduler.generate_plan(all_tasks, pet_map=pet_map, today=TODAY, use_weighted_sort=True)
display_plan(weighted_plan, "WEIGHTED SCHEDULE", "⚡")

# ── Pending tasks ──────────────────────────────────────────────────────────────
section("PENDING TASKS", "⏳")
rows = []
for t in scheduler.filter_by_status(all_tasks, completed=False):
    pet = pet_map.get(id(t))
    rows.append([
        fmt_task(t),
        fmt_pet(pet),
        fmt_priority(t.priority),
        f"{t.duration} min",
        t.recurring or "—",
    ])
print(tabulate(rows, headers=["Task", "Pet", "Priority", "Duration", "Recurring"],
               tablefmt="rounded_outline"))

# ── Completed tasks ────────────────────────────────────────────────────────────
section("COMPLETED TASKS", "✅")
rows = []
for t in scheduler.filter_by_status(all_tasks, completed=True):
    pet = pet_map.get(id(t))
    rows.append([
        fmt_task(t),
        fmt_pet(pet),
        fmt_priority(t.priority),
        f"{t.duration} min",
        t.last_done or "—",
    ])
if rows:
    print(tabulate(rows, headers=["Task", "Pet", "Priority", "Duration", "Completed On"],
                   tablefmt="rounded_outline"))
else:
    print(f"  {C.DIM}(none){C.RESET}")

# ── Recurring reschedule demo ──────────────────────────────────────────────────
section("RECURRING RESCHEDULE DEMO", "🔄")
morning_walk = next(t for t in rex.tasks if t.name == "Morning Walk")
print(f"  {C.DIM}Before:{C.RESET}  {C.BOLD}{morning_walk.name}{C.RESET}"
      f"  completed={fmt_status(morning_walk.completed)}"
      f"  last_done={C.DIM}{morning_walk.last_done}{C.RESET}")

next_walk = rex.complete_task(morning_walk, TODAY)

print(f"  {C.DIM}After: {C.RESET}  {C.BOLD}{morning_walk.name}{C.RESET}"
      f"  completed={fmt_status(morning_walk.completed)}"
      f"  last_done={C.GREEN}{morning_walk.last_done}{C.RESET}")

if next_walk:
    print()
    print(tabulate([
        ["Next occurrence",  next_walk.name,                                     fmt_status(next_walk.completed)],
        ["is_due today",     "—",            f"{C.CYAN}{next_walk.is_due(TODAY)}{C.RESET}"],
        ["days_until_next",  "—",            f"{C.CYAN}{next_walk.days_until_next(TODAY)} day(s){C.RESET}"],
        ["next_due_date",    "—",            f"{C.CYAN}{next_walk.next_due_date()}{C.RESET}"],
    ], tablefmt="rounded_outline"))

print(f"\n  {C.BOLD}Rex{C.RESET} now has {C.CYAN}{len(rex.tasks)}{C.RESET} tasks (new occurrence appended)")

# ── Filter by pet ──────────────────────────────────────────────────────────────
for pet_name, pet_icon in (("Luna", "🐈"), ("Rex", "🐕")):
    section(f"{pet_name.upper()}'S TASKS  (filter_by_pet)", pet_icon)
    rows = []
    for t in scheduler.filter_by_pet(all_tasks, pet_name, pet_map):
        due = t.next_due_date() or "—"
        rows.append([
            fmt_task(t),
            fmt_priority(t.priority),
            fmt_status(t.completed),
            t.recurring or "—",
            due,
        ])
    print(tabulate(rows, headers=["Task", "Priority", "Status", "Recurring", "Next Due"],
                   tablefmt="rounded_outline"))
