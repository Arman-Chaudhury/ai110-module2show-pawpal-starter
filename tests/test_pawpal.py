from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler, ScheduledTask


# ===========================================================================
# Helper
# ===========================================================================

def make_owner(minutes=240):
    owner = Owner(name="Jordan", available_minutes=minutes)
    return owner


# ===========================================================================
# Task — basic completion
# ===========================================================================

def test_mark_complete_changes_status():
    """mark_complete() should flip completed from False to True."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_completed_task_excluded_from_schedule():
    """A completed task should not appear in the generated schedule."""
    owner = make_owner()
    pet = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    done = Task("Old walk", 30, "high")
    done.mark_complete()
    pet.add_task(done)
    schedule = Scheduler(owner=owner).generate_schedule()
    assert all(st.task.title != "Old walk" for st in schedule)


# ===========================================================================
# Task — recurrence logic
# ===========================================================================

def test_daily_task_creates_next_day_instance():
    """Marking a daily task complete should return a new task due tomorrow."""
    task = Task("Morning walk", 30, "high", frequency="daily", due_date=date.today())
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.completed is False
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert next_task.title == task.title


def test_weekly_task_creates_next_week_instance():
    """Marking a weekly task complete should return a new task due in 7 days."""
    task = Task("Bath time", 20, "medium", frequency="weekly", due_date=date.today())
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(weeks=1)


def test_once_task_returns_none_on_complete():
    """A one-off task should return None (no next occurrence)."""
    task = Task("Vet visit", 60, "high", frequency="once")
    result = task.mark_complete()
    assert result is None


def test_complete_task_requeues_recurring_in_pet():
    """pet.complete_task() should add the next occurrence to the pet's task list."""
    pet = Pet(name="Mochi", species="dog", age=3)
    task = Task("Feeding", 10, "high", frequency="daily")
    pet.add_task(task)
    assert len(pet.get_tasks()) == 1
    pet.complete_task(task)
    # Original marked done + new pending instance added
    assert len(pet.get_tasks()) == 2
    assert pet.get_tasks()[0].completed is True
    assert pet.get_tasks()[1].completed is False


def test_complete_task_does_not_requeue_once():
    """pet.complete_task() on a 'once' task should NOT add a new task."""
    pet = Pet(name="Luna", species="cat", age=2)
    task = Task("Vet visit", 60, "high", frequency="once")
    pet.add_task(task)
    pet.complete_task(task)
    assert len(pet.get_tasks()) == 1   # still only the original (now done)


# ===========================================================================
# Pet — task management
# ===========================================================================

def test_add_task_increases_task_count():
    """Adding a task to a Pet should increase its task count by 1."""
    pet = Pet(name="Luna", species="cat", age=5)
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task("Feeding", 10, "high", "feed"))
    assert len(pet.get_tasks()) == 1


def test_add_task_stamps_pet_name():
    """Pet.add_task() should set the task's pet_name to the pet's name."""
    pet = Pet(name="Mochi", species="dog", age=3)
    task = Task("Walk", 30, "high")
    pet.add_task(task)
    assert task.pet_name == "Mochi"


def test_pet_with_no_tasks_produces_empty_schedule():
    """A pet with zero tasks should result in an empty schedule."""
    owner = make_owner()
    owner.add_pet(Pet(name="Ghost", species="cat", age=1))
    schedule = Scheduler(owner=owner).generate_schedule()
    assert schedule == []


# ===========================================================================
# Owner
# ===========================================================================

def test_owner_get_all_tasks_aggregates_across_pets():
    """Owner.get_all_tasks() should return tasks from all pets combined."""
    owner = make_owner()
    dog = Pet(name="Mochi", species="dog", age=3)
    cat = Pet(name="Luna",  species="cat", age=5)
    dog.add_task(Task("Walk",    30, "high"))
    cat.add_task(Task("Feeding", 10, "high"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    assert len(owner.get_all_tasks()) == 2


# ===========================================================================
# Scheduler — sorting
# ===========================================================================

def test_sort_by_time_returns_chronological_order():
    """sort_by_time() should order: morning → anytime → afternoon → evening."""
    owner = make_owner()
    scheduler = Scheduler(owner=owner)
    tasks = [
        Task("E", 10, "low",  preferred_time="evening"),
        Task("A", 10, "low",  preferred_time="afternoon"),
        Task("M", 10, "low",  preferred_time="morning"),
        Task("X", 10, "low",  preferred_time="anytime"),
    ]
    sorted_tasks = scheduler.sort_by_time(tasks)
    order = [t.preferred_time for t in sorted_tasks]
    assert order == ["morning", "anytime", "afternoon", "evening"]


def test_sort_by_time_stable_within_same_slot():
    """Tasks in the same slot should not be reordered relative to each other."""
    owner = make_owner()
    scheduler = Scheduler(owner=owner)
    tasks = [
        Task("First",  10, "high", preferred_time="morning"),
        Task("Second", 10, "low",  preferred_time="morning"),
    ]
    sorted_tasks = scheduler.sort_by_time(tasks)
    assert sorted_tasks[0].title == "First"
    assert sorted_tasks[1].title == "Second"


# ===========================================================================
# Scheduler — filtering
# ===========================================================================

def test_filter_by_pet_name_returns_only_that_pet():
    """filter_tasks(pet_name=X) should return only tasks belonging to pet X."""
    owner = make_owner()
    dog = Pet(name="Mochi", species="dog", age=3)
    cat = Pet(name="Luna",  species="cat", age=5)
    dog.add_task(Task("Walk",    30, "high"))
    cat.add_task(Task("Feeding", 10, "high"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner=owner)
    mochi_tasks = scheduler.filter_tasks(pet_name="Mochi")
    assert all(t.pet_name == "Mochi" for t in mochi_tasks)
    assert len(mochi_tasks) == 1


def test_filter_completed_false_excludes_done_tasks():
    """filter_tasks(completed=False) should not return any completed tasks."""
    owner = make_owner()
    pet = Pet(name="Mochi", species="dog", age=3)
    done = Task("Old walk", 30, "high")
    done.mark_complete()
    pet.add_task(done)
    pet.add_task(Task("New walk", 30, "high"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    pending = scheduler.filter_tasks(completed=False)
    assert all(not t.completed for t in pending)
    assert len(pending) == 1


# ===========================================================================
# Scheduler — core scheduling
# ===========================================================================

def test_schedule_respects_available_time():
    """Scheduler should not exceed owner's available_minutes."""
    owner = make_owner(minutes=30)
    pet = Pet(name="Buddy", species="dog", age=4)
    owner.add_pet(pet)
    pet.add_task(Task("Long walk",  30, "high"))
    pet.add_task(Task("Short task", 10, "medium"))   # would exceed limit
    schedule = Scheduler(owner=owner).generate_schedule()
    total = sum(st.task.duration_minutes for st in schedule)
    assert total <= owner.available_minutes


def test_high_priority_scheduled_before_low():
    """High-priority tasks should appear before low-priority ones (same slot)."""
    owner = make_owner()
    pet = Pet(name="Noodle", species="cat", age=1)
    owner.add_pet(pet)
    pet.add_task(Task("Play", 20, "low",  preferred_time="anytime"))
    pet.add_task(Task("Meds", 10, "high", preferred_time="anytime"))
    schedule = Scheduler(owner=owner).generate_schedule()
    titles = [st.task.title for st in schedule]
    assert titles.index("Meds") < titles.index("Play")


# ===========================================================================
# Scheduler — conflict detection
# ===========================================================================

def test_detect_conflicts_finds_overlap():
    """Two tasks that overlap in time should produce a conflict warning."""
    owner = make_owner()
    scheduler = Scheduler(owner=owner)
    t1 = Task("Walk",     30, "high")
    t2 = Task("Grooming", 20, "medium")
    overlapping = [
        ScheduledTask(task=t1, start_time="08:00", reason=""),
        ScheduledTask(task=t2, start_time="08:15", reason=""),  # starts inside t1
    ]
    warnings = scheduler.detect_conflicts(overlapping)
    assert len(warnings) == 1
    assert "CONFLICT" in warnings[0] or "conflict" in warnings[0].lower()


def test_detect_conflicts_exact_same_start_time():
    """Two tasks at the exact same start time should be flagged as a conflict."""
    owner = make_owner()
    scheduler = Scheduler(owner=owner)
    t1 = Task("Feeding", 10, "high")
    t2 = Task("Meds",    5,  "high")
    same_time = [
        ScheduledTask(task=t1, start_time="08:00", reason=""),
        ScheduledTask(task=t2, start_time="08:00", reason=""),
    ]
    warnings = scheduler.detect_conflicts(same_time)
    assert len(warnings) >= 1


def test_detect_conflicts_no_overlap_returns_empty():
    """Sequential non-overlapping tasks should produce zero conflict warnings."""
    owner = make_owner()
    scheduler = Scheduler(owner=owner)
    t1 = Task("Walk",    30, "high")
    t2 = Task("Feeding", 10, "high")
    sequential = [
        ScheduledTask(task=t1, start_time="08:00", reason=""),
        ScheduledTask(task=t2, start_time="08:30", reason=""),  # starts exactly when t1 ends
    ]
    warnings = scheduler.detect_conflicts(sequential)
    assert warnings == []


def test_generated_schedule_has_no_conflicts():
    """A schedule produced by generate_schedule() should never have conflicts."""
    owner = make_owner(minutes=180)
    pet = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    pet.add_task(Task("Walk",     30, "high",   "walk",   "morning"))
    pet.add_task(Task("Feeding",  10, "high",   "feed",   "morning"))
    pet.add_task(Task("Grooming", 20, "medium", "grooming","evening"))
    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()
    assert scheduler.detect_conflicts(schedule) == []
