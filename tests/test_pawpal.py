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


# --- Priority-based scheduling ---


def test_sort_by_priority_orders_high_medium_low_then_shortest():
    long_high = Task("Long walk", 30, "high", due_date=DAY)
    low = Task("Brush", 5, "low", due_date=DAY)
    short_high = Task("Feed", 10, "high", due_date=DAY)
    medium = Task("Play", 20, "medium", due_date=DAY)
    scheduler = make_dated_scheduler(long_high, low, short_high, medium)

    result = scheduler.sort_by_priority()

    assert result == [short_high, long_high, medium, low]


@pytest.mark.parametrize("available_time", [0, 15, 45, 60, 100])
def test_schedule_never_exceeds_available_time(available_time):
    scheduler = make_dated_scheduler(
        Task("Walk", 30, "high", due_date=DAY),
        Task("Feed", 10, "high", due_date=DAY),
        Task("Play", 20, "medium", due_date=DAY),
        Task("Bath", 40, "medium", due_date=DAY),
        Task("Brush", 15, "low", due_date=DAY),
    )
    scheduler.owner.set_available_time(available_time)

    plan = scheduler.generate_schedule(for_date=DAY)

    total = sum(task.duration_minutes for task in plan)
    assert total <= available_time


def test_zero_available_time_gives_empty_plan():
    walk = Task("Walk", 30, "high", due_date=DAY)
    feed = Task("Feed", 10, "medium", due_date=DAY)
    scheduler = make_dated_scheduler(walk, feed)
    scheduler.owner.set_available_time(0)

    plan = scheduler.generate_schedule(for_date=DAY)

    assert plan == []
    assert scheduler.skipped == [walk, feed]
    for task in scheduler.skipped:
        assert scheduler.get_skip_reason(task) == "not enough time left"


def test_task_longer_than_available_time_is_skipped_but_smaller_ones_fit():
    big_walk = Task("Big walk", 45, "high", due_date=DAY)
    feed = Task("Feed", 10, "low", due_date=DAY)
    scheduler = make_dated_scheduler(big_walk, feed)
    scheduler.owner.set_available_time(30)

    plan = scheduler.generate_schedule(for_date=DAY)

    assert plan == [feed]
    assert scheduler.skipped == [big_walk]
    assert scheduler.get_skip_reason(big_walk) == "not enough time left"


# --- More task validation and conflicts ---


@pytest.mark.parametrize("bad_duration", [0, -5])
def test_zero_or_negative_duration_is_rejected(bad_duration):
    with pytest.raises(ValueError):
        Task("Walk", bad_duration)


def test_tasks_with_identical_start_times_conflict():
    walk = Task("Walk", 30, pet_name="Rex", start_time="08:00")
    feed = Task("Feed", 10, pet_name="Mia", start_time="08:00")
    scheduler = make_dated_scheduler()

    assert scheduler.detect_conflicts([walk, feed]) == [(walk, feed)]


# --- Scheduling edge cases ---


@pytest.mark.parametrize(
    "durations, available_time",
    [
        ([45], 45),  # one task exactly fills the time
        ([30, 20, 10], 60),  # several tasks exactly fill the time
    ],
)
def test_exact_fit_is_scheduled(durations, available_time):
    tasks = [Task(f"Task {n}", minutes, due_date=DAY) for n, minutes in enumerate(durations)]
    scheduler = make_dated_scheduler(*tasks)
    scheduler.owner.set_available_time(available_time)

    plan = scheduler.generate_schedule(for_date=DAY)

    assert len(plan) == len(tasks)
    assert sum(task.duration_minutes for task in plan) == available_time
    assert scheduler.skipped == []


def test_empty_schedule_when_owner_has_no_pets():
    scheduler = Scheduler(Owner("Sam", available_time=60))

    plan = scheduler.generate_schedule(for_date=DAY)

    assert plan == []
    assert scheduler.skipped == []
    assert "No schedule yet" in scheduler.explain_schedule()


def test_empty_schedule_when_pet_has_no_tasks():
    scheduler = make_dated_scheduler()  # one pet, no tasks

    plan = scheduler.generate_schedule(for_date=DAY)

    assert plan == []
    assert scheduler.skipped == []


def test_regenerating_schedule_replaces_old_plan():
    walk = Task("Walk", 30, "high", due_date=DAY)
    feed = Task("Feed", 10, "high", due_date=DAY)
    play = Task("Play", 20, "medium", due_date=DAY)
    scheduler = make_dated_scheduler(walk, feed, play)
    scheduler.owner.set_available_time(60)
    scheduler.generate_schedule(for_date=DAY)

    scheduler.owner.set_available_time(40)
    plan = scheduler.generate_schedule(for_date=DAY)

    assert plan == [feed, walk]
    assert scheduler.skipped == [play]


def test_regenerating_with_same_settings_does_not_add_duplicates():
    scheduler = make_dated_scheduler(Task("Walk", 30, due_date=DAY))

    scheduler.generate_schedule(for_date=DAY)
    plan = scheduler.generate_schedule(for_date=DAY)

    assert len(plan) == 1


# --- Pets and owners ---


def test_pet_with_no_tasks():
    pet = Pet("Rex", "Dog", 3)

    assert pet.view_tasks() == []
    assert pet.get_info() == "Rex (Dog, 3 years old) - 0 task(s)"


def test_negative_available_time_is_rejected_when_creating_owner():
    with pytest.raises(ValueError):
        Owner("Sam", available_time=-1)


def test_negative_available_time_is_rejected_by_setter_and_old_value_kept():
    owner = Owner("Sam", available_time=45)

    with pytest.raises(ValueError):
        owner.set_available_time(-10)

    assert owner.available_time == 45


# --- Sorting and validation edge cases ---


def test_sort_by_time_keeps_original_order_for_identical_times():
    first = Task("Walk", 30, start_time="08:00")
    second = Task("Feed", 10, start_time="08:00")
    earlier = Task("Meds", 5, start_time="07:00")
    scheduler = make_dated_scheduler()

    assert scheduler.sort_by_time([first, second, earlier]) == [earlier, first, second]
    assert scheduler.sort_by_time([second, first]) == [second, first]


@pytest.mark.parametrize(
    "priority, frequency",
    [
        ("urgent", "daily"),  # unknown priority
        ("High", "daily"),  # priorities are lowercase
        ("medium", "monthly"),  # unknown frequency
        ("medium", ""),  # empty frequency
    ],
)
def test_invalid_priority_or_frequency_is_rejected(priority, frequency):
    with pytest.raises(ValueError):
        Task("Walk", 30, priority, frequency)


# --- Recurring task edge cases ---


def test_mark_complete_then_complete_task_creates_no_occurrence():
    pet = Pet("Rex", "Dog", 3)
    walk = Task("Walk", 30, frequency="daily", due_date=DAY)
    pet.add_task(walk)
    walk.mark_complete()

    result = pet.complete_task(walk)

    assert result is None
    assert len(pet.tasks) == 1


def test_overdue_daily_task_next_due_is_based_on_old_due_date():
    pet = Pet("Rex", "Dog", 3)
    overdue = Task("Walk", 30, frequency="daily", due_date=DAY - timedelta(days=3))
    pet.add_task(overdue)

    next_task = pet.complete_task(overdue)

    # One day after the original due date, not one day after it was completed.
    assert next_task.due_date == DAY - timedelta(days=2)


# --- Low-priority extras ---


@pytest.mark.parametrize(
    "field_name, new_value",
    [
        ("priority", "low"),
        ("title", "Run"),
        ("duration_minutes", 45),
        ("frequency", "once"),
        ("start_time", "09:00"),
    ],
)
def test_update_task_changes_only_the_given_field(field_name, new_value):
    task = Task("Walk", 30, "high", "weekly", start_time="08:00", due_date=DAY)
    before = copy.copy(task)

    task.update_task(**{field_name: new_value})

    assert getattr(task, field_name) == new_value
    for other_field in ["title", "duration_minutes", "priority", "frequency", "start_time", "due_date", "completed"]:
        if other_field != field_name:
            assert getattr(task, other_field) == getattr(before, other_field)


def test_get_all_tasks_combines_pets_including_one_with_no_tasks():
    owner = Owner("Sam", available_time=60)
    rex = Pet("Rex", "Dog", 3)
    mia = Pet("Mia", "Cat", 2)  # no tasks
    walk = Task("Walk", 30)
    play = Task("Play", 20)
    rex.add_task(walk)
    rex.add_task(play)
    owner.add_pet(rex)
    owner.add_pet(mia)

    assert owner.get_all_tasks() == [walk, play]


def test_recurring_task_chain_moves_forward_one_day_each_time():
    pet = Pet("Rex", "Dog", 3)
    walk = Task("Walk", 30, frequency="daily", due_date=DAY)
    pet.add_task(walk)

    second_walk = pet.complete_task(walk)
    third_walk = pet.complete_task(second_walk)
    repeat = pet.complete_task(walk)  # already done, so nothing new

    assert third_walk.due_date == DAY + timedelta(days=2)
    assert repeat is None
    assert [task.due_date for task in pet.tasks] == [
        DAY,
        DAY + timedelta(days=1),
        DAY + timedelta(days=2),
    ]


@pytest.mark.parametrize(
    "tasks",
    [
        [],
        [Task("Walk", 30, start_time="08:00")],
    ],
)
def test_fewer_than_two_tasks_have_no_conflicts(tasks):
    scheduler = make_dated_scheduler()

    assert scheduler.detect_conflicts(tasks) == []


def test_three_tasks_all_overlapping_give_three_pairs():
    walk = Task("Walk", 60, start_time="08:00")  # 08:00-09:00
    feed = Task("Feed", 30, start_time="08:15")  # 08:15-08:45
    meds = Task("Meds", 20, start_time="08:30")  # 08:30-08:50
    scheduler = make_dated_scheduler()

    conflicts = scheduler.detect_conflicts([walk, feed, meds])

    assert conflicts == [(walk, feed), (walk, meds), (feed, meds)]


def test_conflict_warning_shows_24_00_for_task_ending_at_midnight():
    night_walk = Task("Night walk", 60, pet_name="Rex", start_time="23:00")
    meds = Task("Meds", 10, pet_name="Mia", start_time="23:30")
    scheduler = make_dated_scheduler()

    conflicts = scheduler.detect_conflicts([night_walk, meds])

    assert len(conflicts) == 1
    assert scheduler.format_conflict(*conflicts[0]) == (
        "WARNING: Night walk (Rex) 23:00-24:00 overlaps with Meds (Mia) 23:30-23:40."
    )
