import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Smart daily care planning for your pets.")

# ---------------------------------------------------------------------------
# Session state — Owner object persists across all reruns
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

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
        if st.form_submit_button("Create owner profile"):
            st.session_state.owner = Owner(name=owner_name, available_minutes=int(available))
            st.rerun()
else:
    owner: Owner = st.session_state.owner
    st.success(f"Owner: **{owner.name}** — {owner.available_minutes} min available today")
    if st.button("Reset (start over)"):
        st.session_state.owner = None
        st.rerun()

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
    if st.form_submit_button("Add pet"):
        owner.add_pet(Pet(name=pet_name, species=species, age=int(age)))
        st.rerun()

if owner.pets:
    st.table([
        {"Name": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.tasks)}
        for p in owner.pets
    ])
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
        col3, col4, col5, col6, col7 = st.columns(5)
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
        with col7:
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
        if st.form_submit_button("Add task"):
            target = next(p for p in owner.pets if p.name == selected_pet)
            target.add_task(Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                category=category,
                preferred_time=preferred_time,
                frequency=frequency,
            ))
            st.rerun()

    # Show tasks sorted by time slot (using Scheduler.sort_by_time)
    scheduler = Scheduler(owner=owner)
    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.markdown("**All tasks — sorted by time slot**")
        sorted_tasks = scheduler.sort_by_time(all_tasks)
        st.table([
            {
                "Pet":      t.pet_name,
                "Time":     t.preferred_time,
                "Title":    t.title,
                "Duration": t.duration_minutes,
                "Priority": t.priority,
                "Freq":     t.frequency,
                "Done":     t.completed,
            }
            for t in sorted_tasks
        ])

        # Show pending-only filter per pet
        with st.expander("Filter: pending tasks by pet"):
            filter_pet = st.selectbox("Show pending tasks for", pet_names, key="filter_pet")
            pending_for_pet = scheduler.filter_tasks(pet_name=filter_pet, completed=False)
            if pending_for_pet:
                st.table([
                    {"Title": t.title, "Priority": t.priority,
                     "Duration": t.duration_minutes, "Freq": t.frequency}
                    for t in pending_for_pet
                ])
            else:
                st.success(f"All tasks for {filter_pet} are complete!")

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — Generate schedule
# ---------------------------------------------------------------------------
st.subheader("4. Generate Today's Schedule")

pending = [t for t in owner.get_all_tasks() if not t.completed]

if not pending:
    st.info("No pending tasks to schedule. Add tasks above.")
else:
    if st.button("Generate schedule", type="primary"):
        scheduler = Scheduler(owner=owner)
        schedule = scheduler.generate_schedule()

        if not schedule:
            st.warning("No tasks fit within your available time today.")
        else:
            total_min = sum(s.task.duration_minutes for s in schedule)
            st.success(
                f"Scheduled **{len(schedule)} tasks** — "
                f"{total_min} / {owner.available_minutes} min used"
            )

            # Conflict warnings — shown before the schedule table
            conflicts = scheduler.detect_conflicts(schedule)
            for w in conflicts:
                st.warning(w)

            # Schedule display
            for item in schedule:
                cols = st.columns([1, 3, 1, 1, 1])
                cols[0].markdown(f"**{item.start_time}**")
                cols[1].markdown(item.task.title)
                cols[2].markdown(f"`{item.task.priority}`")
                cols[3].markdown(f"{item.task.duration_minutes} min")
                cols[4].markdown(f"🔁 {item.task.frequency}" if item.task.frequency != "once" else "")
                st.caption(f"↳ {item.reason}")

            if not conflicts:
                st.success("No scheduling conflicts detected.")

st.divider()

# ---------------------------------------------------------------------------
# Section 5 — Mark tasks complete
# ---------------------------------------------------------------------------
st.subheader("5. Mark Tasks Complete")

all_tasks = owner.get_all_tasks()
pending_tasks = [t for t in all_tasks if not t.completed]

if not pending_tasks:
    st.info("No pending tasks.")
else:
    pet_map = {p.name: p for p in owner.pets}
    task_labels = [f"{t.pet_name} — {t.title} ({t.frequency})" for t in pending_tasks]
    choice = st.selectbox("Select a task to mark complete", task_labels)
    if st.button("Mark complete"):
        idx = task_labels.index(choice)
        chosen_task = pending_tasks[idx]
        pet = pet_map[chosen_task.pet_name]
        pet.complete_task(chosen_task)   # re-queues automatically if recurring
        if chosen_task.frequency != "once":
            st.success(
                f"'{chosen_task.title}' marked done. "
                f"Next {chosen_task.frequency} occurrence added automatically."
            )
        else:
            st.success(f"'{chosen_task.title}' marked complete.")
        st.rerun()
