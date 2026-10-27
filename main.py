"""PawPal+ demo: build an owner with pets and tasks, then print today's schedule."""

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
        reason = "already completed" if task.completed else "not enough time left"
        print(
            f"  - {task.pet_name}: {task.title} "
            f"({task.duration_minutes} min, {task.priority}) -> {reason}"
        )


def main() -> None:
    owner = Owner("Sam", available_time=60)

    rex = Pet("Rex", "Dog", 3)
    mia = Pet("Mia", "Cat", 2)

    rex.add_task(Task("Walk", 30, "high"))
    mia.add_task(Task("Feed", 10, "high"))
    rex.add_task(Task("Play", 20, "medium"))
    mia.add_task(Task("Groom", 15, "low"))

    owner.add_pet(rex)
    owner.add_pet(mia)

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()
    print_schedule(scheduler)


if __name__ == "__main__":
    main()
