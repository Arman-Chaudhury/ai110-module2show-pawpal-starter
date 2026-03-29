import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Step 2: Manage application memory via st.session_state
# The Owner object (and everything it contains) lives here so it survives
# every rerun caused by button clicks or widget interactions.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None   # not yet created

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------
st.subheader("1. Owner Setup")

if st.session_state.owner is None:
    with st.form("owner_form"):
        owner_name = st.text_input("Your name", value="Jordan")
        available = st.number_input(
            "Minutes available for pet care today",
            min_value=10, max_value=480, value=120, step=10,
        )
        submitted = st.form_submit_button("Create owner profile")
    if submitted:
        # Step 3: wire UI action → Owner class
        st.session_state.owner = Owner(name=owner_name, available_minutes=int(available))
        st.rerun()
else:
    owner: Owner = st.session_state.owner
    st.success(
        f"Owner: **{owner.name}** — {owner.available_minutes} min available today"
    )
    if st.button("Reset owner (start over)"):
        st.session_state.owner = None
        st.rerun()

# Nothing below here makes sense without an owner
if st.session_state.owner is None:
    st.stop()

owner: Owner = st.session_state.owner

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Pet management
# ---------------------------------------------------------------------------
st.subheader("2. Your Pets")

with st.form("add_pet_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)
    add_pet = st.form_submit_button("Add pet")

if add_pet:
    # Step 3: wire UI action → Pet + owner.add_pet()
    new_pet = Pet(name=pet_name, species=species, age=int(age))
    owner.add_pet(new_pet)
    st.rerun()

if owner.pets:
    pet_rows = [
        {"Name": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.tasks)}
        for p in owner.pets
    ]
    st.table(pet_rows)
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Task management
# ---------------------------------------------------------------------------
st.subheader("3. Add Care Tasks")

if not owner.pets:
    st.warning("Add at least one pet before adding tasks.")
else:
    pet_names = [p.name for p in owner.pets]

    with st.form("add_task_form"):
        col1, col2 = st.columns(2)
        with col1:
            selected_pet = st.selectbox("Pet", pet_names)
        with col2:
            task_title = st.text_input("Task title", value="Morning walk")
        col3, col4, col5, col6 = st.columns(4)
        with col3:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=30)
        with col4:
            priority = st.selectbox("Priority", ["high", "medium", "low"])
        with col5:
            category = st.selectbox(
                "Category", ["walk", "feed", "meds", "grooming", "enrichment", "general"]
            )
        with col6:
            preferred_time = st.selectbox(
                "Preferred time", ["morning", "afternoon", "evening", "anytime"]
            )
        add_task = st.form_submit_button("Add task")

    if add_task:
        # Step 3: wire UI action → Task + pet.add_task()
        target_pet = next(p for p in owner.pets if p.name == selected_pet)
        target_pet.add_task(
            Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                category=category,
                preferred_time=preferred_time,
            )
        )
        st.rerun()

    # Show all tasks grouped by pet
    for pet in owner.pets:
        if pet.tasks:
            st.markdown(f"**{pet.name}'s tasks**")
            rows = [
                {
                    "Title": t.title,
                    "Duration": t.duration_minutes,
                    "Priority": t.priority,
                    "Category": t.category,
                    "Time": t.preferred_time,
                    "Done": t.completed,
                }
                for t in pet.tasks
            ]
            st.table(rows)

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — Generate schedule
# ---------------------------------------------------------------------------
st.subheader("4. Generate Today's Schedule")

all_tasks = owner.get_all_tasks()
pending = [t for t in all_tasks if not t.completed]

if not pending:
    st.info("No pending tasks to schedule. Add tasks above.")
else:
    if st.button("Generate schedule", type="primary"):
        scheduler = Scheduler(owner=owner)
        schedule = scheduler.generate_schedule()

        if not schedule:
            st.warning("No tasks fit within your available time today.")
        else:
            st.success(f"Scheduled {len(schedule)} tasks — {sum(s.task.duration_minutes for s in schedule)} min total")
            for st_item in schedule:
                with st.container():
                    cols = st.columns([1, 3, 1, 1])
                    cols[0].markdown(f"**{st_item.start_time}**")
                    cols[1].markdown(f"{st_item.task.title}")
                    cols[2].markdown(f"`{st_item.task.priority}`")
                    cols[3].markdown(f"{st_item.task.duration_minutes} min")
                    st.caption(f"↳ {st_item.reason}")
