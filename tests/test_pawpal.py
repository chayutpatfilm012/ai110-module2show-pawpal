import copy
from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

# A fixed date so the recurrence tests give the same result every day.
DAY = date(2026, 1, 10)


def test_mark_complete_sets_completed_to_true():
    task = Task("Walk", 30, "high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_adds_task_to_pet():
    pet = Pet("Rex", "Dog", 3)
    task = Task("Feed", 10, "high")
    starting_count = len(pet.tasks)

    pet.add_task(task)

    assert len(pet.tasks) == starting_count + 1
    assert task in pet.tasks


def make_scheduler():
    """Build an owner with two pets and a few tasks for the tests below."""
    owner = Owner("Sam", available_time=60)
    rex = Pet("Rex", "Dog", 3)
    mia = Pet("Mia", "Cat", 2)
    rex.add_task(Task("Walk", 30, "high", start_time="09:00"))
    rex.add_task(Task("Play", 20, "medium", start_time="12:15"))
    mia.add_task(Task("Feed", 10, "high", start_time="07:30"))
    mia.add_task(Task("Groom", 15, "low"))
    owner.add_pet(rex)
    owner.add_pet(mia)
    return Scheduler(owner)


# --- Sorting by time ---


def test_sort_by_time_puts_earliest_first_and_untimed_last():
    scheduler = make_scheduler()
    tasks = scheduler.owner.get_all_tasks()

    result = scheduler.sort_by_time(tasks)

    assert [task.title for task in result] == ["Feed", "Walk", "Play", "Groom"]


def test_sort_by_time_does_not_change_original_list():
    scheduler = make_scheduler()
    tasks = scheduler.owner.get_all_tasks()
    original_order = list(tasks)

    scheduler.sort_by_time(tasks)

    assert tasks == original_order


def test_sort_by_time_defaults_to_daily_plan():
    scheduler = make_scheduler()
    scheduler.generate_schedule()  # priority-based: Feed, Walk, Play (60 min)

    result = scheduler.sort_by_time()

    assert [task.title for task in scheduler.daily_plan] == ["Feed", "Walk", "Play"]
    assert [task.title for task in result] == ["Feed", "Walk", "Play"]


@pytest.mark.parametrize("bad_time", ["25:00", "12:60", "8:30", "abc", "08-30", "0830"])
def test_invalid_start_time_is_rejected(bad_time):
    with pytest.raises(ValueError):
        Task("Walk", 30, start_time=bad_time)


def test_task_must_end_by_midnight():
    with pytest.raises(ValueError):
        Task("Late walk", 45, start_time="23:30")
    Task("Last walk", 60, start_time="23:00")  # ends exactly at 24:00, allowed


def test_update_task_rejects_bad_start_time_and_keeps_old_value():
    task = Task("Walk", 30, start_time="08:00")

    with pytest.raises(ValueError):
        task.update_task(start_time="99:99")

    assert task.start_time == "08:00"


# --- Filtering ---


def test_filter_by_pet_name():
    scheduler = make_scheduler()

    result = scheduler.filter_tasks(pet_name="Rex")

    assert [task.title for task in result] == ["Walk", "Play"]


def test_filter_by_completed_status():
    scheduler = make_scheduler()
    scheduler.owner.pets[0].tasks[0].mark_complete()  # Rex's Walk

    done = scheduler.filter_tasks(completed=True)
    not_done = scheduler.filter_tasks(completed=False)

    assert [task.title for task in done] == ["Walk"]
    assert [task.title for task in not_done] == ["Play", "Feed", "Groom"]


def test_filter_by_pet_and_completed_together():
    scheduler = make_scheduler()
    scheduler.owner.pets[0].tasks[0].mark_complete()  # Rex's Walk

    result = scheduler.filter_tasks(pet_name="Rex", completed=False)

    assert [task.title for task in result] == ["Play"]


def test_filter_with_no_arguments_returns_all_tasks():
    scheduler = make_scheduler()

    assert len(scheduler.filter_tasks()) == 4


def test_filter_with_no_matches_returns_empty_list():
    scheduler = make_scheduler()

    assert scheduler.filter_tasks(pet_name="Buddy") == []


def test_filter_does_not_change_pet_task_lists():
    scheduler = make_scheduler()

    scheduler.filter_tasks(pet_name="Rex")

    assert len(scheduler.owner.pets[1].tasks) == 2


# --- Recurring tasks ---


def test_daily_task_next_occurrence_is_one_day_later():
    task = Task("Walk", 30, "high", frequency="daily", start_time="07:00", due_date=DAY)
    task.pet_name = "Rex"

    next_task = task.next_occurrence()

    assert next_task.due_date == DAY + timedelta(days=1)
    assert (next_task.title, next_task.duration_minutes, next_task.priority) == ("Walk", 30, "high")
    assert (next_task.frequency, next_task.pet_name, next_task.start_time) == ("daily", "Rex", "07:00")


def test_weekly_task_next_occurrence_is_seven_days_later():
    task = Task("Bath", 25, frequency="weekly", due_date=DAY)

    assert task.next_occurrence().due_date == DAY + timedelta(days=7)


def test_once_task_does_not_recur():
    task = Task("Vet visit", 45, frequency="once", due_date=DAY)

    assert task.next_occurrence() is None


def test_next_occurrence_starts_incomplete_and_leaves_original_alone():
    task = Task("Walk", 30, due_date=DAY)
    task.mark_complete()

    next_task = task.next_occurrence()

    assert next_task.completed is False
    assert task.completed is True
    assert task.due_date == DAY


def test_complete_task_adds_next_occurrence_to_pet():
    pet = Pet("Rex", "Dog", 3)
    walk = Task("Walk", 30, due_date=DAY)
    pet.add_task(walk)

    next_task = pet.complete_task(walk)

    assert walk.completed is True
    assert len(pet.tasks) == 2
    assert pet.tasks[1] is next_task
    assert next_task.due_date == DAY + timedelta(days=1)


def test_complete_once_task_adds_nothing():
    pet = Pet("Rex", "Dog", 3)
    vet = Task("Vet visit", 45, frequency="once", due_date=DAY)
    pet.add_task(vet)

    assert pet.complete_task(vet) is None
    assert vet.completed is True
    assert len(pet.tasks) == 1


def test_completing_same_task_twice_does_not_duplicate():
    pet = Pet("Rex", "Dog", 3)
    walk = Task("Walk", 30, due_date=DAY)
    pet.add_task(walk)

    pet.complete_task(walk)
    second_result = pet.complete_task(walk)

    assert second_result is None
    assert len(pet.tasks) == 2


def test_completed_task_stays_in_history():
    pet = Pet("Rex", "Dog", 3)
    walk = Task("Walk", 30, due_date=DAY)
    pet.add_task(walk)

    pet.complete_task(walk)

    assert pet.tasks[0] is walk
    assert pet.tasks[0].completed is True


def test_complete_task_rejects_task_from_another_pet():
    rex = Pet("Rex", "Dog", 3)
    mia = Pet("Mia", "Cat", 2)
    feed = Task("Feed", 10)
    mia.add_task(feed)

    with pytest.raises(ValueError):
        rex.complete_task(feed)
    assert feed.completed is False


def make_dated_scheduler(*tasks):
    """Build an owner with one pet holding the given tasks."""
    owner = Owner("Sam", available_time=120)
    pet = Pet("Rex", "Dog", 3)
    for task in tasks:
        pet.add_task(task)
    owner.add_pet(pet)
    return Scheduler(owner)


def test_future_task_is_not_scheduled():
    future = Task("Walk", 30, due_date=DAY + timedelta(days=1))
    scheduler = make_dated_scheduler(future)

    scheduler.generate_schedule(for_date=DAY)

    assert future not in scheduler.daily_plan
    assert future not in scheduler.skipped


def test_overdue_unfinished_task_is_scheduled():
    overdue = Task("Walk", 30, due_date=DAY - timedelta(days=2))
    scheduler = make_dated_scheduler(overdue)

    scheduler.generate_schedule(for_date=DAY)

    assert scheduler.daily_plan == [overdue]


def test_old_completed_task_is_ignored():
    old = Task("Walk", 30, due_date=DAY - timedelta(days=1))
    old.mark_complete()
    scheduler = make_dated_scheduler(old)

    scheduler.generate_schedule(for_date=DAY)

    assert scheduler.daily_plan == []
    assert scheduler.skipped == []


def test_completed_task_due_today_is_skipped_with_reason():
    done = Task("Walk", 30, due_date=DAY)
    done.mark_complete()
    scheduler = make_dated_scheduler(done)

    scheduler.generate_schedule(for_date=DAY)

    assert scheduler.skipped == [done]
    assert scheduler.get_skip_reason(done) == "already completed"


def test_next_occurrence_is_scheduled_on_its_due_date():
    pet_scheduler = make_dated_scheduler(Task("Walk", 30, due_date=DAY))
    pet = pet_scheduler.owner.pets[0]
    next_walk = pet.complete_task(pet.tasks[0])

    today_plan = list(pet_scheduler.generate_schedule(for_date=DAY))
    tomorrow_plan = pet_scheduler.generate_schedule(for_date=DAY + timedelta(days=1))

    assert today_plan == []
    assert tomorrow_plan == [next_walk]


# --- Conflict detection ---


def test_overlapping_tasks_are_detected():
    walk = Task("Walk", 30, pet_name="Rex", start_time="08:00")
    feed = Task("Feed", 10, pet_name="Rex", start_time="08:15")
    scheduler = make_dated_scheduler()

    assert scheduler.detect_conflicts([walk, feed]) == [(walk, feed)]


def test_tasks_touching_at_endpoints_do_not_conflict():
    walk = Task("Walk", 30, start_time="08:00")  # ends 08:30
    groom = Task("Groom", 15, start_time="08:30")
    scheduler = make_dated_scheduler()

    assert scheduler.detect_conflicts([walk, groom]) == []


def test_tasks_without_start_time_are_ignored():
    walk = Task("Walk", 30, start_time="08:00")
    anytime = Task("Brush", 60)  # no start_time
    scheduler = make_dated_scheduler()

    assert scheduler.detect_conflicts([walk, anytime]) == []


def test_conflict_between_different_pets_is_detected():
    walk = Task("Walk", 30, pet_name="Rex", start_time="08:00")
    feed = Task("Feed", 10, pet_name="Mia", start_time="08:15")
    scheduler = make_dated_scheduler()

    conflicts = scheduler.detect_conflicts([walk, feed])

    assert len(conflicts) == 1
    assert scheduler.format_conflict(*conflicts[0]) == (
        "WARNING: Walk (Rex) 08:00-08:30 overlaps with Feed (Mia) 08:15-08:25."
    )


def test_multiple_overlapping_pairs_are_detected():
    # A long task overlaps two later tasks that don't overlap each other.
    long_walk = Task("Long walk", 120, start_time="08:00")  # 08:00-10:00
    feed = Task("Feed", 10, start_time="08:30")  # 08:30-08:40
    play = Task("Play", 15, start_time="09:00")  # 09:00-09:15
    scheduler = make_dated_scheduler()

    conflicts = scheduler.detect_conflicts([long_walk, feed, play])

    assert conflicts == [(long_walk, feed), (long_walk, play)]


def test_detect_conflicts_does_not_modify_tasks():
    tasks = [
        Task("Walk", 30, start_time="08:00"),
        Task("Feed", 10, start_time="08:15"),
    ]
    before = copy.deepcopy(tasks)
    scheduler = make_dated_scheduler()

    scheduler.detect_conflicts(tasks)

    assert tasks == before


def test_detect_conflicts_uses_daily_plan_by_default():
    walk = Task("Walk", 30, "high", start_time="08:00")
    feed = Task("Feed", 10, "high", start_time="08:15")
    # Too long to fit after Walk and Feed, so it is skipped, not planned.
    bath = Task("Bath", 100, "low", start_time="08:20")
    scheduler = make_dated_scheduler(walk, feed, bath)  # 120 minutes available
    scheduler.generate_schedule()

    conflicts = scheduler.detect_conflicts()

    assert bath in scheduler.skipped
    assert conflicts == [(feed, walk)]  # daily_plan order: shorter high task first
