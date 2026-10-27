"""PawPal+ demo: build an owner with pets and tasks, then print today's schedule."""

from datetime import date, timedelta
from typing import Optional

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(scheduler: Scheduler) -> None:
    """Print the scheduler's daily plan and skipped tasks as a simple table."""
    owner = scheduler.owner
    total = sum(task.duration_minutes for task in scheduler.daily_plan)

    print("=" * 50)
    print(f"Today's Schedule for {owner.name}")
    print("=" * 50)
    print(f"{'#':<3}{'Pet':<8}{'Task':<16}{'Duration':<11}{'Priority'}")
    print("-" * 50)
    for number, task in enumerate(scheduler.daily_plan, start=1):
        print(
            f"{number:<3}{task.pet_name:<8}{task.title:<16}"
            f"{str(task.duration_minutes) + ' min':<11}{task.priority}"
        )
    print("-" * 50)
    print(f"Total scheduled: {total} of {owner.available_time} minutes")

    print()
    print("Skipped tasks:")
    if not scheduler.skipped:
        print("  (none)")
    for task in scheduler.skipped:
        print(
            f"  - {task.pet_name}: {task.title} "
            f"({task.duration_minutes} min, {task.priority}) -> {scheduler.get_skip_reason(task)}"
        )


def print_task_list(heading: str, tasks: list[Task]) -> None:
    """Print a heading and one line per task, showing its start time and status."""
    print()
    print(heading)
    if not tasks:
        print("  (no matching tasks)")
    for task in tasks:
        time = task.start_time or "anytime"
        status = "done" if task.completed else "to do"
        print(f"  {time:<9}{task.pet_name:<6}{task.title:<8}({task.priority}, {status})")


def print_task_history(pet: Pet) -> None:
    """Print every task a pet has, including completed ones, with its due date."""
    print()
    print(f"{pet.name}'s task history:")
    for task in pet.tasks:
        status = "done" if task.completed else "to do"
        print(f"  {task.due_date}  {task.title:<10}{task.frequency:<8}{status}")


def describe_new_task(old_task: Task, new_task: Optional[Task]) -> None:
    """Print what happened when a task was completed."""
    if new_task is None:
        print(f"  Completed '{old_task.title}' ({old_task.frequency}) -> no new task created")
    else:
        print(
            f"  Completed '{old_task.title}' due {old_task.due_date} ({old_task.frequency}) "
            f"-> next one due {new_task.due_date}"
        )


def main() -> None:
    owner = Owner("Sam", available_time=60)

    rex = Pet("Rex", "Dog", 3)
    mia = Pet("Mia", "Cat", 2)

    rex.add_task(Task("Walk", 30, "high", start_time="07:00"))
    feed = Task("Feed", 10, "high", start_time="08:00")
    mia.add_task(feed)
    rex.add_task(Task("Play", 20, "medium", start_time="17:30"))
    mia.add_task(Task("Groom", 15, "low"))  # no start time: can happen any time

    owner.add_pet(rex)
    owner.add_pet(mia)

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()
    print_schedule(scheduler)

    # --- Sorting by time ---
    print()
    print("=" * 50)
    print("Sorting by Time")
    print("=" * 50)
    print_task_list("Today's plan in clock order:", scheduler.sort_by_time())
    print_task_list("All tasks in clock order:", scheduler.sort_by_time(owner.get_all_tasks()))

    # --- Filtering ---
    feed.mark_complete()
    print()
    print("=" * 50)
    print("Filtering Tasks (after marking Mia's Feed as done)")
    print("=" * 50)
    print_task_list("Rex's tasks:", scheduler.filter_tasks(pet_name="Rex"))
    print_task_list("Tasks still to do:", scheduler.filter_tasks(completed=False))
    print_task_list("Mia's completed tasks:", scheduler.filter_tasks(pet_name="Mia", completed=True))
    print_task_list("Tasks for a pet named Buddy:", scheduler.filter_tasks(pet_name="Buddy"))

    # --- Recurring tasks ---
    print()
    print("=" * 50)
    print("Recurring Tasks Demo")
    print("=" * 50)

    walk = rex.tasks[0]  # daily (the default frequency)
    bath = Task("Bath", 25, "medium", frequency="weekly")
    rex.add_task(bath)
    vet = Task("Vet visit", 45, "high", frequency="once")
    mia.add_task(vet)

    describe_new_task(walk, rex.complete_task(walk))
    describe_new_task(bath, rex.complete_task(bath))
    describe_new_task(vet, mia.complete_task(vet))

    print()
    print("Completing the same Walk again:")
    if rex.complete_task(walk) is None:
        print("  Walk was already done -> no duplicate task created")

    print_task_history(rex)
    print_task_history(mia)

    tomorrow = date.today() + timedelta(days=1)
    scheduler.generate_schedule(for_date=tomorrow)
    print()
    print(f"Plan for tomorrow ({tomorrow}):")
    for task in scheduler.daily_plan:
        print(f"  {task.pet_name}: {task.title} ({task.duration_minutes} min, due {task.due_date})")
    for task in scheduler.skipped:
        print(f"  skipped {task.pet_name}: {task.title} -> {scheduler.get_skip_reason(task)}")

    # --- Conflict detection ---
    # These example tasks are separate from the pets above, so the
    # recurring task history and earlier demos are not affected.
    print()
    print("=" * 50)
    print("Conflict Detection Demo")
    print("=" * 50)
    example_tasks = [
        Task("Walk", 30, "high", pet_name="Rex", start_time="08:00"),
        Task("Feed", 10, "high", pet_name="Mia", start_time="08:15"),
        Task("Groom", 15, "low", pet_name="Mia", start_time="08:30"),
    ]
    print_task_list("Example tasks:", example_tasks)

    conflicts = scheduler.detect_conflicts(example_tasks)
    print()
    print(f"{len(conflicts)} conflict(s) found:")
    for task_a, task_b in conflicts:
        print(f"  {scheduler.format_conflict(task_a, task_b)}")


if __name__ == "__main__":
    main()
