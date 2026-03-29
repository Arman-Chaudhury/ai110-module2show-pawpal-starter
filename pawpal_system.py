from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
TIME_ORDER     = {"morning": 0, "anytime": 1, "afternoon": 2, "evening": 3}

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


def _time_to_minutes(time_str: str) -> int:
    """Convert HH:MM string to minutes-since-midnight."""
    h, m = map(int, time_str.split(":"))
    return h * 60 + m


@dataclass
class Task:
    """Represents a single pet care activity."""
    title: str
    duration_minutes: int
    priority: str               # "low", "medium", "high"
    category: str = "general"  # "walk", "feed", "meds", "grooming", "enrichment"
    preferred_time: str = "anytime"  # "morning", "afternoon", "evening", "anytime"
    completed: bool = False
    frequency: str = "once"    # "once", "daily", "weekly"
    due_date: date = field(default_factory=date.today)
    pet_name: str = ""         # stamped automatically by Pet.add_task()

    def mark_complete(self) -> Optional["Task"]:
        """
        Mark this task done.
        If it is recurring (daily/weekly), return a new Task for the next
        occurrence with an updated due_date; otherwise return None.
        """
        self.completed = True
        if self.frequency == "daily":
            return Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                category=self.category,
                preferred_time=self.preferred_time,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(days=1),
                pet_name=self.pet_name,
            )
        if self.frequency == "weekly":
            return Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                category=self.category,
                preferred_time=self.preferred_time,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(weeks=1),
                pet_name=self.pet_name,
            )
        return None


@dataclass
class Pet:
    """Stores pet details and a list of care tasks."""
    name: str
    species: str    # "dog", "cat", "other"
    age: int
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task and stamp its pet_name for later filtering."""
        task.pet_name = self.name
        self.tasks.append(task)

    def get_tasks(self) -> List[Task]:
        """Return all tasks for this pet."""
        return self.tasks

    def complete_task(self, task: Task) -> None:
        """Mark a task complete and re-queue it if it is a recurring task."""
        next_task = task.mark_complete()
        if next_task is not None:
            self.tasks.append(next_task)


@dataclass
class Owner:
    """Manages multiple pets and provides access to all their tasks."""
    name: str
    available_minutes: int = 480    # total care time per day (default 8 h)
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
    """The 'brain' — retrieves, sorts, filters, schedules, and checks tasks."""
    owner: Owner

    # ------------------------------------------------------------------
    # Step 2: Sorting
    # ------------------------------------------------------------------
    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks chronologically by preferred time slot using a lambda key."""
        return sorted(tasks, key=lambda t: TIME_ORDER.get(t.preferred_time, 1))

    # ------------------------------------------------------------------
    # Step 2: Filtering
    # ------------------------------------------------------------------
    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Task]:
        """
        Filter all owner tasks by pet name and/or completion status.
        Pass pet_name=None to include all pets.
        Pass completed=None to include both done and pending tasks.
        """
        tasks = self.owner.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name == pet_name]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    # ------------------------------------------------------------------
    # Step 4: Conflict detection
    # ------------------------------------------------------------------
    def detect_conflicts(self, schedule: List["ScheduledTask"]) -> List[str]:
        """
        Check every pair of scheduled tasks for time overlap.
        Returns a list of human-readable warning strings (empty = no conflicts).
        Uses a lightweight O(n²) scan: compares start/end minutes for each pair
        and flags any pair where one task starts before the other ends.
        """
        warnings = []
        for i in range(len(schedule)):
            for j in range(i + 1, len(schedule)):
                a, b = schedule[i], schedule[j]
                a_start = _time_to_minutes(a.start_time)
                a_end   = a_start + a.task.duration_minutes
                b_start = _time_to_minutes(b.start_time)
                b_end   = b_start + b.task.duration_minutes
                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"WARNING — conflict: '{a.task.title}' "
                        f"({a.start_time}, {a.task.duration_minutes} min) overlaps "
                        f"'{b.task.title}' ({b.start_time}, {b.task.duration_minutes} min)"
                    )
        return warnings

    # ------------------------------------------------------------------
    # Core schedule generation
    # ------------------------------------------------------------------
    def generate_schedule(self) -> List["ScheduledTask"]:
        """
        Build an ordered daily schedule.
        - Skips completed tasks.
        - Sorts by priority (high → medium → low).
        - Respects preferred_time slot; uses slot cursors to place tasks
          sequentially within each slot.
        - Stops once owner's available_minutes are exhausted.
        - Returns schedule sorted chronologically.
        """
        pending = [t for t in self.owner.get_all_tasks() if not t.completed]
        sorted_tasks = sorted(pending, key=lambda t: PRIORITY_ORDER.get(t.priority, 2))

        slot_cursor = dict(SLOT_START)
        minutes_used = 0
        schedule: List[ScheduledTask] = []

        for task in sorted_tasks:
            if minutes_used + task.duration_minutes > self.owner.available_minutes:
                continue
            slot = task.preferred_time if task.preferred_time in slot_cursor else "anytime"
            start_time = _minutes_to_time(slot_cursor[slot])
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
    """A Task placed into the daily schedule with a start time and reasoning."""
    task: Task
    start_time: str     # e.g. "08:00"
    reason: str
