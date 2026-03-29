from pawpal_system import Owner, Pet, Task, Scheduler


# --- Task tests ---

def test_mark_complete_changes_status():
    """mark_complete() should flip completed from False to True."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_completed_task_excluded_from_schedule():
    """A completed task should not appear in the generated schedule."""
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)

    done_task = Task("Old walk", 30, "high")
    done_task.mark_complete()
    pet.add_task(done_task)

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()
    assert all(st.task.title != "Old walk" for st in schedule)


# --- Pet task-addition tests ---

def test_add_task_increases_task_count():
    """Adding a task to a Pet should increase its task count by 1."""
    pet = Pet(name="Luna", species="cat", age=5)
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task("Feeding", 10, "high", "feed"))
    assert len(pet.get_tasks()) == 1


def test_add_multiple_tasks():
    """All added tasks should be retrievable from the pet."""
    pet = Pet(name="Mochi", species="dog", age=2)
    pet.add_task(Task("Walk",     30, "high",   "walk"))
    pet.add_task(Task("Feeding",  10, "high",   "feed"))
    pet.add_task(Task("Grooming", 15, "low",    "grooming"))
    assert len(pet.get_tasks()) == 3


# --- Scheduler tests ---

def test_schedule_respects_available_time():
    """Scheduler should not exceed owner's available_minutes."""
    owner = Owner(name="Alex", available_minutes=30)
    pet = Pet(name="Buddy", species="dog", age=4)
    owner.add_pet(pet)
    pet.add_task(Task("Long walk",  30, "high"))
    pet.add_task(Task("Short task", 10, "medium"))   # would exceed limit

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()
    total = sum(st.task.duration_minutes for st in schedule)
    assert total <= owner.available_minutes


def test_high_priority_scheduled_before_low():
    """High-priority tasks should appear before low-priority ones."""
    owner = Owner(name="Sam", available_minutes=120)
    pet = Pet(name="Noodle", species="cat", age=1)
    owner.add_pet(pet)
    # Add low first so insertion order can't carry the answer
    pet.add_task(Task("Play", 20, "low",  preferred_time="anytime"))
    pet.add_task(Task("Meds", 10, "high", preferred_time="anytime"))

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()
    titles = [st.task.title for st in schedule]
    assert titles.index("Meds") < titles.index("Play")


def test_owner_get_all_tasks_aggregates_across_pets():
    """Owner.get_all_tasks() should return tasks from all pets combined."""
    owner = Owner(name="Jordan", available_minutes=240)
    dog = Pet(name="Mochi", species="dog", age=3)
    cat = Pet(name="Luna",  species="cat", age=5)
    dog.add_task(Task("Walk",    30, "high"))
    cat.add_task(Task("Feeding", 10, "high"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    assert len(owner.get_all_tasks()) == 2
