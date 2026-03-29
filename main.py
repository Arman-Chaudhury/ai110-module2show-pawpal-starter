from pawpal_system import Owner, Pet, Task, Scheduler, ScheduledTask

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
owner = Owner(name="Jordan", available_minutes=120)

dog = Pet(name="Mochi", species="dog", age=3)
cat = Pet(name="Luna",  species="cat", age=5)

owner.add_pet(dog)
owner.add_pet(cat)

# Tasks added out of order (evening before morning) to test sorting
dog.add_task(Task("Evening walk",      30, "medium", "walk",       "evening"))
dog.add_task(Task("Morning walk",      30, "high",   "walk",       "morning",  frequency="daily"))
dog.add_task(Task("Breakfast feeding", 10, "high",   "feed",       "morning"))
dog.add_task(Task("Medication",         5, "high",   "meds",       "morning",  frequency="daily"))
dog.add_task(Task("Teeth brushing",    10, "low",    "grooming",   "evening"))

cat.add_task(Task("Breakfast feeding", 10, "high",   "feed",       "morning"))
cat.add_task(Task("Litter box clean",  10, "medium", "general",    "anytime",  frequency="daily"))
cat.add_task(Task("Play / enrichment", 20, "low",    "enrichment", "afternoon"))

scheduler = Scheduler(owner=owner)

# ---------------------------------------------------------------------------
# Step 2a: Sort by time — tasks added out of order, sorted by time slot
# ---------------------------------------------------------------------------
print("=" * 50)
print("ALL TASKS SORTED BY TIME SLOT")
print("=" * 50)
all_tasks = owner.get_all_tasks()
for t in scheduler.sort_by_time(all_tasks):
    print(f"  [{t.preferred_time:10}] {t.pet_name:6} — {t.title}")

# ---------------------------------------------------------------------------
# Step 2b: Filter tasks by pet and completion status
# ---------------------------------------------------------------------------
print("\n" + "=" * 50)
print("FILTER: Mochi's pending tasks only")
print("=" * 50)
for t in scheduler.filter_tasks(pet_name="Mochi", completed=False):
    print(f"  {t.title} ({t.priority})")

# ---------------------------------------------------------------------------
# Step 3: Recurring tasks — mark a daily task complete, check re-queue
# ---------------------------------------------------------------------------
print("\n" + "=" * 50)
print("RECURRING TASK DEMO")
print("=" * 50)
morning_walk = next(t for t in dog.get_tasks() if t.title == "Morning walk")
print(f"  Before: Mochi has {len(dog.get_tasks())} tasks, "
      f"'Morning walk' completed={morning_walk.completed}, due={morning_walk.due_date}")

dog.complete_task(morning_walk)

next_walk = dog.get_tasks()[-1]
print(f"  After:  Mochi has {len(dog.get_tasks())} tasks, "
      f"original completed={morning_walk.completed}")
print(f"  New instance: '{next_walk.title}' completed={next_walk.completed}, "
      f"due={next_walk.due_date} (tomorrow)")

# ---------------------------------------------------------------------------
# Main schedule (uses remaining pending tasks)
# ---------------------------------------------------------------------------
print("\n" + "=" * 50)
schedule = scheduler.generate_schedule()
print(scheduler.explain_plan(schedule))

# ---------------------------------------------------------------------------
# Step 4: Conflict detection — manually construct two overlapping tasks
# ---------------------------------------------------------------------------
print("\n" + "=" * 50)
print("CONFLICT DETECTION DEMO")
print("=" * 50)
t1 = Task("Extra grooming",  30, "medium", "grooming",  "morning")
t2 = Task("Nail trim",       20, "low",    "grooming",  "morning")
overlapping = [
    ScheduledTask(task=t1, start_time="08:00", reason="demo"),
    ScheduledTask(task=t2, start_time="08:15", reason="demo — overlaps t1"),
]
conflicts = scheduler.detect_conflicts(overlapping)
if conflicts:
    for w in conflicts:
        print(f"  {w}")
else:
    print("  No conflicts detected.")

print("\nNo conflicts in main schedule:")
for w in scheduler.detect_conflicts(schedule) or ["  None — schedule is clean."]:
    print(f"  {w}")
