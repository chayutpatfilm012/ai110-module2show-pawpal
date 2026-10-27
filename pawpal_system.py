"""PawPal+ system classes, translated from diagrams/uml.mmd."""

from dataclasses import dataclass, field
from typing import Optional

# Priority strings don't sort in priority order alphabetically,
# so the Scheduler uses these numbers when sorting (higher = more important).
PRIORITY_ORDER = {"low": 1, "medium": 2, "high": 3}
FREQUENCIES = ("once", "daily", "weekly")


def _check_task_values(duration_minutes: int, priority: str, frequency: str) -> None:
    """Raise ValueError if any task value is invalid."""
    if duration_minutes <= 0:
        raise ValueError("duration_minutes must be a positive number")
    if priority not in PRIORITY_ORDER:
        raise ValueError(f"priority must be one of {list(PRIORITY_ORDER)}")
    if frequency not in FREQUENCIES:
        raise ValueError(f"frequency must be one of {list(FREQUENCIES)}")


@dataclass
class Task:
    """A single pet care task, such as a walk or feeding."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low", "medium", or "high"
    frequency: str = "daily"  # "once", "daily", or "weekly"
    completed: bool = False
    pet_name: str = ""  # which pet this task belongs to

    def __post_init__(self) -> None:
        """Check that the new task's duration, priority, and frequency are valid."""
        _check_task_values(self.duration_minutes, self.priority, self.frequency)

    def update_task(
        self,
        title: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        priority: Optional[str] = None,
        frequency: Optional[str] = None,
    ) -> None:
        """Change any of the task's details. Leave an argument out to keep its value."""
        new_title = title if title is not None else self.title
        new_duration = duration_minutes if duration_minutes is not None else self.duration_minutes
        new_priority = priority if priority is not None else self.priority
        new_frequency = frequency if frequency is not None else self.frequency

        # Check everything first so a bad value doesn't leave the task half-updated.
        _check_task_values(new_duration, new_priority, new_frequency)

        self.title = new_title
        self.duration_minutes = new_duration
        self.priority = new_priority
        self.frequency = new_frequency

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def get_details(self) -> str:
        """Return a readable description of this task."""
        status = "done" if self.completed else "to do"
        pet = f" for {self.pet_name}" if self.pet_name else ""
        return (
            f"{self.title}{pet}: {self.duration_minutes} min, "
            f"{self.priority} priority, {self.frequency} ({status})"
        )


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Label any tasks given when the pet is created with the pet's name."""
        for task in self.tasks:
            task.pet_name = self.name

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet and label it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def view_tasks(self) -> list[Task]:
        """Return this pet's tasks."""
        return list(self.tasks)

    def get_info(self) -> str:
        """Return a readable description of this pet."""
        return f"{self.name} ({self.species}, {self.age} years old) - {len(self.tasks)} task(s)"


@dataclass
class Owner:
    """A pet owner with limited time and personal preferences."""

    name: str
    available_time: int = 0  # minutes per day
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Make sure the owner's starting available time is not negative."""
        if self.available_time < 0:
            raise ValueError("available_time cannot be negative")

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def set_available_time(self, minutes: int) -> None:
        """Set how many minutes the owner has for pet care today."""
        if minutes < 0:
            raise ValueError("available_time cannot be negative")
        self.available_time = minutes

    def update_preferences(self, preferences: dict) -> None:
        """Add or change preferences. Existing keys not in `preferences` are kept."""
        self.preferences.update(preferences)

    def get_all_tasks(self) -> list[Task]:
        """Return every task from every pet."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks


@dataclass
class Scheduler:
    """Builds a daily plan of tasks that fits the owner's available time.

    Tasks come from owner.pets and the time limit from owner.available_time.
    """

    owner: Owner
    daily_plan: list[Task] = field(default_factory=list)
    skipped: list[Task] = field(default_factory=list)

    def sort_by_priority(self) -> list[Task]:
        """Return all of the owner's pets' tasks, highest priority first.

        Priority strings are mapped to numbers using PRIORITY_ORDER.
        Tasks with the same priority are ordered shortest first.
        """
        return sorted(
            self.owner.get_all_tasks(),
            key=lambda task: (-PRIORITY_ORDER[task.priority], task.duration_minutes),
        )

    def generate_schedule(self) -> list[Task]:
        """Choose tasks that fit in the available time and save them as the daily plan.

        Goes through tasks from most to least important and adds each one
        that still fits. Completed tasks and tasks that don't fit go in `skipped`.
        """
        self.daily_plan = []
        self.skipped = []
        time_used = 0

        for task in self.sort_by_priority():
            if task.completed:
                self.skipped.append(task)
            elif time_used + task.duration_minutes <= self.owner.available_time:
                self.daily_plan.append(task)
                time_used += task.duration_minutes
            else:
                self.skipped.append(task)

        return self.daily_plan

    def explain_schedule(self) -> str:
        """Explain why each task was or wasn't included in the plan."""
        if not self.daily_plan and not self.skipped:
            return "No schedule yet. Add tasks and call generate_schedule() first."

        total = sum(task.duration_minutes for task in self.daily_plan)
        lines = [
            f"Daily plan for {self.owner.name}: "
            f"{total} of {self.owner.available_time} minutes used."
        ]

        lines.append("Scheduled:")
        if self.daily_plan:
            for number, task in enumerate(self.daily_plan, start=1):
                lines.append(f"  {number}. {task.get_details()}")
        else:
            lines.append("  (nothing fit in the available time)")

        if self.skipped:
            lines.append("Skipped:")
            for task in self.skipped:
                reason = "already completed" if task.completed else "not enough time left"
                lines.append(f"  - {task.get_details()} -> {reason}")

        return "\n".join(lines)
