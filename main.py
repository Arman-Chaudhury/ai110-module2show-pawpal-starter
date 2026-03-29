from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=120)

dog = Pet(name="Mochi", species="dog", age=3)
cat = Pet(name="Luna", species="cat", age=5)

owner.add_pet(dog)
owner.add_pet(cat)

# --- Tasks for Mochi ---
dog.add_task(Task("Morning walk",      30, "high",   "walk",       "morning"))
dog.add_task(Task("Breakfast feeding", 10, "high",   "feed",       "morning"))
dog.add_task(Task("Medication",        5,  "high",   "meds",       "morning"))
dog.add_task(Task("Evening walk",      30, "medium", "walk",       "evening"))
dog.add_task(Task("Teeth brushing",    10, "low",    "grooming",   "evening"))

# --- Tasks for Luna ---
cat.add_task(Task("Breakfast feeding", 10, "high",   "feed",       "morning"))
cat.add_task(Task("Litter box clean",  10, "medium", "general",    "anytime"))
cat.add_task(Task("Play / enrichment", 20, "low",    "enrichment", "afternoon"))

# --- Generate schedule ---
scheduler = Scheduler(owner=owner)
schedule = scheduler.generate_schedule()

# --- Print ---
print(scheduler.explain_plan(schedule))
