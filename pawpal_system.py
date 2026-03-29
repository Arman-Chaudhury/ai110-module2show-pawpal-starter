from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Owner:
    """Represents the pet owner and their scheduling constraints."""
    name: str
    available_minutes: int = 480  # default 8 hours per day
    preferences: List[str] = field(default_factory=list)  # e.g. ["morning walks"]

    def add_pet(self, pet: "Pet") -> None:
        """Associate a pet with this owner."""
        pass

    def update_preferences(self, preferences: List[str]) -> None:
        """Update the owner's scheduling preferences."""
        pass


@dataclass
class Pet:
    """Represents a pet whose care needs are being planned."""
    name: str
    species: str  # "dog", "cat", "other"
    age: int
    owner: Optional["Owner"] = None


@dataclass
class Task:
    """Represents a single pet care task."""
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    category: str = "general"  # "walk", "feed", "meds", "grooming", "enrichment"
    preferred_time: str = "anytime"  # "morning", "afternoon", "evening", "anytime"


@dataclass
class ScheduledTask:
    """A Task that has been placed into a daily schedule with a start time and reasoning."""
    task: Task
    start_time: str  # e.g. "08:00"
    reason: str      # explanation of why/when this task was scheduled


@dataclass
class Scheduler:
    """Builds a daily care plan for a pet given the owner's time constraints and task priorities."""
    owner: Owner
    pet: Pet
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to the pool of tasks to be scheduled."""
        pass

    def generate_schedule(self) -> List[ScheduledTask]:
        """
        Build an ordered daily schedule.
        Prioritizes high-priority tasks first, then fills remaining time
        with lower-priority tasks, respecting preferred_time hints.
        Returns a list of ScheduledTask in chronological order.
        """
        pass

    def explain_plan(self, schedule: List[ScheduledTask]) -> str:
        """Return a human-readable explanation of the generated schedule."""
        pass
