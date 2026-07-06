from datetime import date
from pawpal_system import Category, Owner, Pet, Priority, Scheduler, Task

TODAY = str(date.today())

# --- Owner ---
owner = Owner("Valeria", available_minutes=120, preferences="morning routine")

# --- Pets ---
rex = Pet("Rex", species="dog", breed="Labrador")
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

# --- Shared setup ---
scheduler = Scheduler(owner, start_time="07:00")
all_pet_tasks = owner.all_tasks()
pet_map = {id(task): pet for pet, task in all_pet_tasks}
all_tasks = [task for _, task in all_pet_tasks]

# --- Today's schedule ---
plan = scheduler.generate_plan(all_tasks, pet_map=pet_map, today=TODAY)
print("=" * 45)
print("         PAWPAL — TODAY'S SCHEDULE")
print("=" * 45)
print(plan.display())

# --- Conflict detection ---
print("\n" + "=" * 45)
print("  CONFLICT DETECTION")
print("=" * 45)
conflict_warnings = scheduler.detect_conflicts(all_tasks, pet_map)
if conflict_warnings:
    for w in conflict_warnings:
        print(w)
else:
    print("  No conflicts detected.")

# --- sort_by_time: tasks in chronological order ---
print("\n" + "=" * 45)
print("  SORTED BY TIME (all tasks)")
print("=" * 45)
for t in scheduler.sort_by_time(all_tasks):
    slot = t.preferred_time or "no time"
    pet_name = pet_map[id(t)].name
    print(f"  {slot}  {t.name} ({pet_name})")

# --- sort_by_priority: highest priority first ---
print("\n" + "=" * 45)
print("  SORTED BY PRIORITY (all tasks)")
print("=" * 45)
for t in scheduler.sort_by_priority(all_tasks):
    pet_name = pet_map[id(t)].name
    print(f"  [{t.priority.name}]  {t.name} ({pet_name})")

# --- filter_by_status: pending vs completed ---
print("\n" + "=" * 45)
print("  PENDING TASKS")
print("=" * 45)
for t in scheduler.filter_by_status(all_tasks, completed=False):
    pet_name = pet_map[id(t)].name
    print(f"  {t.name} ({pet_name})")

print("\n" + "=" * 45)
print("  COMPLETED TASKS")
print("=" * 45)
for t in scheduler.filter_by_status(all_tasks, completed=True):
    pet_name = pet_map[id(t)].name
    print(f"  {t.name} ({pet_name})")

# --- Recurring task auto-reschedule ---
print("\n" + "=" * 45)
print("  RECURRING RESCHEDULE DEMO")
print("=" * 45)
morning_walk = next(t for t in rex.tasks if t.name == "Morning Walk")
print(f"  Before:  {morning_walk.name}  completed={morning_walk.completed}  last_done={morning_walk.last_done}")
next_walk = rex.complete_task(morning_walk, TODAY)
print(f"  After:   {morning_walk.name}  completed={morning_walk.completed}  last_done={morning_walk.last_done}")
if next_walk:
    print(f"  Next:    {next_walk.name}  completed={next_walk.completed}  last_done={next_walk.last_done}")
    print(f"           is_due today    → {next_walk.is_due(TODAY)}")
    print(f"           days_until_next → {next_walk.days_until_next(TODAY)} day(s)")
    print(f"           next_due_date   → {next_walk.next_due_date()}")
print(f"  Rex now has {len(rex.tasks)} tasks (new occurrence appended)")

# --- filter_by_pet: isolate one pet's tasks ---
print("\n" + "=" * 45)
print("  LUNA'S TASKS (filter_by_pet)")
print("=" * 45)
for t in scheduler.filter_by_pet(all_tasks, "Luna", pet_map):
    due = f"  next due {t.next_due_date()}" if t.next_due_date() else ""
    print(f"  {t.name}  [{t.priority.name}]  completed={t.completed}{due}")

print("\n" + "=" * 45)
print("  REX'S TASKS (filter_by_pet)")
print("=" * 45)
for t in scheduler.filter_by_pet(all_tasks, "Rex", pet_map):
    due = f"  next due {t.next_due_date()}" if t.next_due_date() else ""
    print(f"  {t.name}  [{t.priority.name}]  completed={t.completed}{due}")
