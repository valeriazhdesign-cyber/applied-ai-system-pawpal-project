import streamlit as st
from pawpal_system import Category, Owner, Pet, Priority, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

with st.expander("About", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

st.divider()

# ── Owner & Pet ────────────────────────────────────────────────────────────────
st.subheader("Owner & Pet")

owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input(
    "Available minutes today", min_value=10, max_value=480, value=120, step=10
)
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

# Create Owner and Pet once per session; reuse on every rerun.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name=owner_name, available_minutes=int(available_minutes)
    )
    pet = Pet(name=pet_name, species=species)
    st.session_state.owner.add_pet(pet)

if "tasks" not in st.session_state:
    st.session_state.tasks = []

st.divider()

# ── Add a Task ─────────────────────────────────────────────────────────────────
st.subheader("Add a Task")

col1, col2 = st.columns(2)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col2:
    category = st.selectbox("Category", [c.value for c in Category])
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

preferred_time = st.text_input("Preferred time (HH:MM, optional)", value="")

if st.button("Add task"):
    task = Task(
        name=task_title,
        category=Category(category),
        duration=int(duration),
        priority=Priority[priority.upper()],
        preferred_time=preferred_time.strip() if preferred_time.strip() else None,
    )
    # Add the task to the first pet via Pet.add_task()
    pet = st.session_state.owner.pets[0]
    pet.add_task(task)
    st.session_state.tasks.append(task)
    st.success(f"Added: {task.name}")

PRIORITY_ICON = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}

if st.session_state.tasks:
    preview_scheduler = Scheduler(st.session_state.owner)

    sort_mode = st.radio(
        "Sort mode",
        ["Priority", "Smart Priority (Weighted)"],
        horizontal=True,
        help=(
            "**Priority** sorts by HIGH → MEDIUM → LOW. "
            "**Smart Priority** also weighs category urgency "
            "(meds > feeding > walk > grooming > enrichment), "
            "whether a recurring task is overdue, and a small "
            "efficiency nudge for shorter tasks."
        ),
    )
    use_weighted = sort_mode == "Smart Priority (Weighted)"

    sorted_tasks = (
        preview_scheduler.sort_by_weighted_priority(st.session_state.tasks)
        if use_weighted
        else preview_scheduler.sort_by_priority(st.session_state.tasks)
    )

    total_task_mins = sum(t.duration for t in sorted_tasks)
    avail = st.session_state.owner.available_minutes
    m1, m2, m3 = st.columns(3)
    m1.metric("Tasks", len(sorted_tasks))
    m2.metric("Total time needed", f"{total_task_mins} min")
    m3.metric("Time available", f"{avail} min", delta=f"{avail - total_task_mins} min")

    label = "Current tasks (smart weighted order):" if use_weighted else "Current tasks (sorted by priority):"
    st.write(label)

    table_rows = []
    for t in sorted_tasks:
        row = {
            "Task": t.name,
            "Priority": f"{PRIORITY_ICON.get(t.priority.name, '')} {t.priority.name}",
            "Category": t.category.value,
            "Duration (min)": t.duration,
            "Time": t.preferred_time or "—",
        }
        if use_weighted:
            row["Urgency Score"] = f"{t.weighted_score():.1f}"
        table_rows.append(row)
    st.table(table_rows)

    pet_map = {id(task): pet for pet, task in st.session_state.owner.all_tasks()}
    conflicts = preview_scheduler.detect_conflicts(sorted_tasks, pet_map=pet_map)
    for conflict in conflicts:
        detail = conflict.strip().removeprefix("WARNING: ")
        st.warning(f"Time conflict: {detail}\n\nTip: Edit the preferred time of one of these tasks above to resolve it.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ── Build Schedule ─────────────────────────────────────────────────────────────
st.subheader("Build Schedule")

start_time = st.text_input("Start time (HH:MM)", value="08:00")

use_weighted_schedule = st.checkbox(
    "Use Smart Priority (Weighted) for schedule",
    value=False,
    help="When checked, the schedule uses the composite urgency score instead of raw priority.",
)

if st.button("Generate schedule"):
    owner = st.session_state.owner
    owner.available_minutes = int(available_minutes)

    all_tasks = [task for _, task in owner.all_tasks()]
    if not all_tasks:
        st.warning("No tasks added yet. Add tasks above first.")
    else:
        scheduler = Scheduler(owner, start_time=start_time.strip() if start_time.strip() else None)

        pet_map = {id(task): pet for pet, task in owner.all_tasks()}
        conflicts = scheduler.detect_conflicts(all_tasks, pet_map=pet_map)
        for conflict in conflicts:
            detail = conflict.strip().removeprefix("WARNING: ")
            st.warning(f"Time conflict: {detail}\n\nTip: Edit the preferred time of one of these tasks to resolve it.")

        plan = scheduler.generate_plan(all_tasks, use_weighted_sort=use_weighted_schedule)

        s1, s2, s3 = st.columns(3)
        s1.metric("Scheduled", len(plan.scheduled_tasks))
        s2.metric("Skipped", len(plan.skipped_tasks))
        s3.metric("Minutes used", f"{plan.total_minutes} / {owner.available_minutes}")

        st.subheader("Scheduled Tasks")
        if plan.scheduled_tasks:
            st.success(f"{len(plan.scheduled_tasks)} task(s) fit within your available time.")
            st.table(
                [
                    {
                        "Time": slot or "—",
                        "Task": t.name,
                        "Priority": f"{PRIORITY_ICON.get(t.priority.name, '')} {t.priority.name}",
                        "Category": t.category.value,
                        "Duration (min)": t.duration,
                    }
                    for t, slot, _ in plan.scheduled_tasks
                ]
            )
        else:
            st.info("No tasks could be scheduled.")

        if plan.skipped_tasks:
            st.subheader("Skipped Tasks")
            st.error(f"{len(plan.skipped_tasks)} task(s) could not fit in your available time.")
            st.table(
                [
                    {
                        "Task": t.name,
                        "Priority": f"{PRIORITY_ICON.get(t.priority.name, '')} {t.priority.name}",
                        "Reason": reason,
                    }
                    for t, reason in plan.skipped_tasks
                ]
            )

        if plan.skipped_tasks:
            st.warning(plan.explanation)
        else:
            st.success(plan.explanation)
