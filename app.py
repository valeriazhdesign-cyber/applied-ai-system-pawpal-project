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

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "Task": t.name,
                "Category": t.category.value,
                "Duration (min)": t.duration,
                "Priority": t.priority.name,
                "Time": t.preferred_time or "—",
            }
            for t in st.session_state.tasks
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ── Build Schedule ─────────────────────────────────────────────────────────────
st.subheader("Build Schedule")

start_time = st.text_input("Start time (HH:MM)", value="08:00")

if st.button("Generate schedule"):
    owner = st.session_state.owner
    owner.available_minutes = int(available_minutes)

    all_tasks = [task for _, task in owner.all_tasks()]
    if not all_tasks:
        st.warning("No tasks added yet. Add tasks above first.")
    else:
        scheduler = Scheduler(owner, start_time=start_time.strip() if start_time.strip() else None)
        plan = scheduler.generate_plan(all_tasks)
        st.text(plan.display())
