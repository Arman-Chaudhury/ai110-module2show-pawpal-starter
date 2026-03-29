from dataclasses import dataclass, field
from typing import List

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# Starting minute-of-day for each time slot (e.g. 480 = 8:00 AM)
SLOT_START = {
    "morning":   480,   # 08:00
    "afternoon": 720,   # 12:00
    "evening":   1020,  # 17:00
    "anytime":   540,   # 09:00
}


def _minutes_to_time(minutes: int) -> str:
    """Convert minutes-since-midnight to HH:MM string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass
class Task:
    """Represents a single pet care activity."""
    title: str
    duration_minutes: int
    priority: str           # "low", "medium", "high"
    category: str = "general"   # "walk", "feed", "meds", "grooming", "enrichment"
    preferred_time: str = "anytime"  # "morning", "afternoon", "evening", "anytime"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True


@dataclass
class Pet:
    """Stores pet details and a list of care tasks."""
    name: str
    species: str    # "dog", "cat", "other"
    age: int
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def get_tasks(self) -> List[Task]:
        """Return all tasks for this pet."""
        return self.tasks


@dataclass
class Owner:
    """Manages multiple pets and provides access to all their tasks."""
    name: str
    available_minutes: int = 480    # total care time available per day (default 8 h)
    preferences: List[str] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Aggregate and return every task across all pets."""
        all_tasks: List[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def update_preferences(self, preferences: List[str]) -> None:
        """Replace the owner's scheduling preferences."""
        self.preferences = preferences


@dataclass
class Scheduler:
    """The 'brain' — retrieves, organises, and schedules tasks across all of an owner's pets."""
    owner: Owner

    def generate_schedule(self) -> List["ScheduledTask"]:
        """
        Build an ordered daily schedule.
        - Skips already-completed tasks.
        - Sorts remaining tasks by priority (high → medium → low).
        - Respects each task's preferred_time slot.
        - Stops adding tasks once the owner's available_minutes are exhausted.
        - Returns the schedule sorted chronologically.
        """
        pending = [t for t in self.owner.get_all_tasks() if not t.completed]
        sorted_tasks = sorted(pending, key=lambda t: PRIORITY_ORDER.get(t.priority, 2))

        # Track current cursor (minutes) for each time slot independently
        slot_cursor = dict(SLOT_START)
        minutes_used = 0
        schedule: List[ScheduledTask] = []

        for task in sorted_tasks:
            if minutes_used + task.duration_minutes > self.owner.available_minutes:
                continue  # not enough time left today

            slot = task.preferred_time if task.preferred_time in slot_cursor else "anytime"
            start = slot_cursor[slot]
            start_time = _minutes_to_time(start)
            reason = (
                f"{task.priority.capitalize()} priority {task.category} task; "
                f"fits in {slot} slot ({task.duration_minutes} min)"
            )
            schedule.append(ScheduledTask(task=task, start_time=start_time, reason=reason))
            slot_cursor[slot] += task.duration_minutes
            minutes_used += task.duration_minutes

        schedule.sort(key=lambda st: st.start_time)
        return schedule

    def explain_plan(self, schedule: List["ScheduledTask"]) -> str:
        """Return a human-readable summary of the generated schedule."""
        if not schedule:
            return "No tasks were scheduled (no pending tasks or no time available)."

        lines = [f"Today's Schedule for {self.owner.name}'s pets", "=" * 45]
        for st in schedule:
            status = "[DONE]" if st.task.completed else "     "
            lines.append(
                f"{st.start_time}  {status}  [{st.task.priority.upper():6}] "
                f"{st.task.title} ({st.task.duration_minutes} min)"
            )
            lines.append(f"               Reason: {st.reason}")

        total = sum(st.task.duration_minutes for st in schedule)
        lines.append("=" * 45)
        lines.append(f"Total: {total} min used / {self.owner.available_minutes} min available")
        return "\n".join(lines)


@dataclass
class ScheduledTask:
    """A Task placed into the daily schedule with a concrete start time and reasoning."""
    task: Task
    start_time: str     # e.g. "08:00"
    reason: str
