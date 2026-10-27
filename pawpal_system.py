"""PawPal+ system classes, translated from diagrams/uml.mmd."""

from dataclasses import dataclass, field
from datetime import date, timedelta
from itertools import combinations
from typing import Optional

# Priority strings don't sort in priority order alphabetically,
# so the Scheduler uses these numbers when sorting (higher = more important).
PRIORITY_ORDER = {"low": 1, "medium": 2, "high": 3}
FREQUENCIES = ("once", "daily", "weekly")
# How many days later the next copy of a recurring task is due.
REPEAT_DAYS = {"daily": 1, "weekly": 7}
MINUTES_PER_DAY = 24 * 60


def _time_to_minutes(start_time: str) -> int:
    """Convert a 24-hour "HH:MM" string to minutes after midnight, e.g. "08:30" -> 510.

    Raises ValueError if the text is not a valid zero-padded time from 00:00 to 23:59.
    """
    error = ValueError(f'start_time must be in 24-hour "HH:MM" format, got "{start_time}"')
    if len(start_time) != 5 or start_time[2] != ":":
        raise error
    hours, minutes = start_time[:2], start_time[3:]
    if not (hours.isdigit() and minutes.isdigit()):
        raise error
    if int(hours) > 23 or int(minutes) > 59:
        raise error
    return int(hours) * 60 + int(minutes)


def _minutes_to_time(minutes: int) -> str:
    """Convert minutes after midnight back to "HH:MM", e.g. 510 -> "08:30"."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _time_range(task: "Task") -> tuple[int, int]:
    """Return a timed task's (start, end) in minutes after midnight."""
    start = _time_to_minutes(task.start_time)
    return start, start + task.duration_minutes


def _check_task_values(
    duration_minutes: int, priority: str, frequency: str, start_time: str = ""
) -> None:
    """Raise ValueError if any task value is invalid."""
    if duration_minutes <= 0:
        raise ValueError("duration_minutes must be a positive number")
    if priority not in PRIORITY_ORDER:
        raise ValueError(f"priority must be one of {list(PRIORITY_ORDER)}")
    if frequency not in FREQUENCIES:
        raise ValueError(f"frequency must be one of {list(FREQUENCIES)}")
    if start_time:
        # Tasks must finish on the same day they start.
        if _time_to_minutes(start_time) + duration_minutes > MINUTES_PER_DAY:
            raise ValueError("task must end by midnight (24:00)")


@dataclass
class Task:
    """A single pet care task, such as a walk or feeding."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low", "medium", or "high"
    frequency: str = "daily"  # "once", "daily", or "weekly"
    completed: bool = False
    pet_name: str = ""  # which pet this task belongs to
    start_time: str = ""  # 24-hour "HH:MM", or "" for any time
    due_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        """Check that the new task's duration, priority, frequency, and start time are valid."""
        _check_task_values(self.duration_minutes, self.priority, self.frequency, self.start_time)

    def update_task(
        self,
        title: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        priority: Optional[str] = None,
        frequency: Optional[str] = None,
        start_time: Optional[str] = None,
    ) -> None:
        """Change any of the task's details. Leave an argument out to keep its value."""
        new_title = title if title is not None else self.title
        new_duration = duration_minutes if duration_minutes is not None else self.duration_minutes
        new_priority = priority if priority is not None else self.priority
        new_frequency = frequency if frequency is not None else self.frequency
        new_start_time = start_time if start_time is not None else self.start_time

        # Check everything first so a bad value doesn't leave the task half-updated.
        _check_task_values(new_duration, new_priority, new_frequency, new_start_time)

        self.title = new_title
        self.duration_minutes = new_duration
        self.priority = new_priority
        self.frequency = new_frequency
        self.start_time = new_start_time

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def next_occurrence(self) -> Optional["Task"]:
        """Return a new, unfinished copy of this task for its next due date.

        Daily tasks repeat 1 day later and weekly tasks 7 days later.
        Returns None for "once" tasks. The original task is not changed.
        """
        if self.frequency not in REPEAT_DAYS:
            return None
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            completed=False,
            pet_name=self.pet_name,
            start_time=self.start_time,
            due_date=self.due_date + timedelta(days=REPEAT_DAYS[self.frequency]),
        )

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

    def complete_task(self, task: Task) -> Optional[Task]:
        """Mark one of this pet's tasks done and add its next occurrence, if it repeats.

        Returns the new task, or None if no new task was added. A task that is
        already completed is left alone, so it can never create a duplicate.
        Raises ValueError if the task does not belong to this pet.
        """
        # Use `is` to find this exact object. `in` would also match a
        # different task that just happens to have the same values.
        if not any(existing is task for existing in self.tasks):
            raise ValueError(f"'{task.title}' is not one of {self.name}'s tasks")
        if task.completed:
            return None

        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            self.add_task(next_task)
        return next_task

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

    def sort_by_time(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return tasks ordered by start time, earliest first, with untimed tasks last.

        Sorts `tasks` if given, otherwise the current daily_plan. The original
        list is not changed. Start times are always validated as zero-padded
        "HH:MM", so comparing them as strings gives the correct clock order.
        """
        if tasks is None:
            tasks = self.daily_plan
        # False sorts before True, so tasks with a start time come first.
        return sorted(tasks, key=lambda task: (task.start_time == "", task.start_time))

    def filter_tasks(
        self, pet_name: Optional[str] = None, completed: Optional[bool] = None
    ) -> list[Task]:
        """Return the owner's tasks that match the given pet and/or completion status.

        Leave an argument as None to skip that filter.
        """
        matches = []
        for task in self.owner.get_all_tasks():
            if pet_name is not None and task.pet_name != pet_name:
                continue
            if completed is not None and task.completed != completed:
                continue
            matches.append(task)
        return matches

    def generate_schedule(self, for_date: Optional[date] = None) -> list[Task]:
        """Choose tasks that fit in the available time and save them as the daily plan.

        Goes through tasks from most to least important and adds each one
        that still fits. Only tasks due on or before `for_date` (default: today)
        are considered. Completed tasks due that day and tasks that don't fit
        go in `skipped`. Future tasks and old completed tasks are left out.
        """
        if for_date is None:
            for_date = date.today()
        self.daily_plan = []
        self.skipped = []
        time_used = 0

        for task in self.sort_by_priority():
            if task.due_date > for_date:
                continue  # not due yet
            if task.completed:
                if task.due_date == for_date:
                    self.skipped.append(task)
                # Completed tasks from earlier days are just history.
            elif time_used + task.duration_minutes <= self.owner.available_time:
                self.daily_plan.append(task)
                time_used += task.duration_minutes
            else:
                self.skipped.append(task)

        return self.daily_plan

    def detect_conflicts(self, tasks: Optional[list[Task]] = None) -> list[tuple[Task, Task]]:
        """Return every pair of tasks whose times overlap.

        Two tasks overlap when each one starts before the other ends; tasks that
        only touch (one ends at 08:30, the next starts at 08:30) do not count.
        Checks `tasks` if given, otherwise the current daily_plan. Tasks without
        a start_time are ignored. Tasks are only reported, never changed or removed.
        """
        if tasks is None:
            tasks = self.daily_plan
        timed_tasks = [task for task in tasks if task.start_time]

        conflicts = []
        # combinations() gives every unique pair once, in list order.
        for task_a, task_b in combinations(timed_tasks, 2):
            start_a, end_a = _time_range(task_a)
            start_b, end_b = _time_range(task_b)
            # Strict < means a task ending at 08:30 doesn't clash with one starting at 08:30.
            if start_a < end_b and start_b < end_a:
                conflicts.append((task_a, task_b))
        return conflicts

    def format_conflict(self, task_a: Task, task_b: Task) -> str:
        """Return a readable warning message for two overlapping tasks."""

        def describe(task: Task) -> str:
            """Return e.g. "Walk (Rex) 08:00-08:30"."""
            start, end = _time_range(task)
            return f"{task.title} ({task.pet_name}) {_minutes_to_time(start)}-{_minutes_to_time(end)}"

        return f"WARNING: {describe(task_a)} overlaps with {describe(task_b)}."

    def get_skip_reason(self, task: Task) -> str:
        """Return why a task in `skipped` was left out of the daily plan."""
        if task.completed:
            return "already completed"
        return "not enough time left"

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
                lines.append(f"  - {task.get_details()} -> {self.get_skip_reason(task)}")

        return "\n".join(lines)
