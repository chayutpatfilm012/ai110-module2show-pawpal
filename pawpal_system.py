"""PawPal+ system classes, translated from diagrams/uml.mmd."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    """A single pet care task, such as a walk or feeding."""

    title: str
    duration_minutes: int
    # "low", "medium", or "high". Strings don't sort in priority order
    # alphabetically, so the Scheduler maps them to numbers when sorting.
    priority: str = "medium"
    completed: bool = False
    pet_name: str = ""  # which pet this task belongs to

    def update_task(
        self,
        title: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        priority: Optional[str] = None,
    ) -> None:
        """Change any of the task's details."""
        pass

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def get_details(self) -> str:
        """Return a readable description of this task."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        pass

    def view_tasks(self) -> list[Task]:
        """Return this pet's tasks."""
        pass

    def get_info(self) -> str:
        """Return a readable description of this pet."""
        pass


@dataclass
class Owner:
    """A pet owner with limited time and personal preferences."""

    name: str
    available_time: int = 0  # minutes per day
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def set_available_time(self, minutes: int) -> None:
        """Set how many minutes the owner has for pet care today."""
        pass

    def update_preferences(self, preferences: dict) -> None:
        """Update the owner's preferences."""
        pass


@dataclass
class Scheduler:
    """Builds a daily plan of tasks that fits the owner's available time.

    Tasks come from owner.pets and the time limit from owner.available_time.
    """

    owner: Owner
    daily_plan: list[Task] = field(default_factory=list)

    def sort_by_priority(self) -> list[Task]:
        """Return all of the owner's pets' tasks, highest priority first.

        Priority strings are mapped to numbers for sorting:
        {"low": 1, "medium": 2, "high": 3}.
        """
        pass

    def generate_schedule(self) -> list[Task]:
        """Choose tasks that fit in the available time and save them as the daily plan."""
        pass

    def explain_schedule(self) -> str:
        """Explain why each task was or wasn't included in the plan."""
        pass
