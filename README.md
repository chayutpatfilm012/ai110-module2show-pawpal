# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

**UML diagrams:** the final architecture is in [diagrams/uml_final.mmd](diagrams/uml_final.mmd); the working diagram used during development is kept in [diagrams/uml.mmd](diagrams/uml.mmd).

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

Output of `python main.py` (recurring task dates depend on the day you run it; this run was on 2026-10-27):

```text
==================================================
Today's Schedule for Sam
==================================================
#  Pet     Task            Duration   Priority
--------------------------------------------------
1  Mia     Feed            10 min     high
2  Rex     Walk            30 min     high
3  Rex     Play            20 min     medium
--------------------------------------------------
Total scheduled: 60 of 60 minutes

Skipped tasks:
  - Mia: Groom (15 min, low) -> not enough time left

==================================================
Sorting by Time
==================================================

Today's plan in clock order:
  07:00    Rex   Walk    (high, to do)
  08:00    Mia   Feed    (high, to do)
  17:30    Rex   Play    (medium, to do)

All tasks in clock order:
  07:00    Rex   Walk    (high, to do)
  08:00    Mia   Feed    (high, to do)
  17:30    Rex   Play    (medium, to do)
  anytime  Mia   Groom   (low, to do)

==================================================
Filtering Tasks (after marking Mia's Feed as done)
==================================================

Rex's tasks:
  07:00    Rex   Walk    (high, to do)
  17:30    Rex   Play    (medium, to do)

Tasks still to do:
  07:00    Rex   Walk    (high, to do)
  17:30    Rex   Play    (medium, to do)
  anytime  Mia   Groom   (low, to do)

Mia's completed tasks:
  08:00    Mia   Feed    (high, done)

Tasks for a pet named Buddy:
  (no matching tasks)

==================================================
Recurring Tasks Demo
==================================================
  Completed 'Walk' due 2026-10-27 (daily) -> next one due 2026-10-28
  Completed 'Bath' due 2026-10-27 (weekly) -> next one due 2026-11-03
  Completed 'Vet visit' (once) -> no new task created

Completing the same Walk again:
  Walk was already done -> no duplicate task created

Rex's task history:
  2026-10-27  Walk      daily   done
  2026-10-27  Play      daily   to do
  2026-10-27  Bath      weekly  done
  2026-10-28  Walk      daily   to do
  2026-11-03  Bath      weekly  to do

Mia's task history:
  2026-10-27  Feed      daily   done
  2026-10-27  Groom     daily   to do
  2026-10-27  Vet visit once    done

Plan for tomorrow (2026-10-28):
  Rex: Walk (30 min, due 2026-10-28)
  Rex: Play (20 min, due 2026-10-27)
  skipped Mia: Groom -> not enough time left

==================================================
Conflict Detection Demo
==================================================

Example tasks:
  08:00    Rex   Walk    (high, to do)
  08:15    Mia   Feed    (high, to do)
  08:30    Mia   Groom   (low, to do)

1 conflict(s) found:
  WARNING: Walk (Rex) 08:00-08:30 overlaps with Feed (Mia) 08:15-08:25.
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest

# Run with coverage (needs the pytest-cov plugin: pip install pytest-cov):
python -m pytest --cov
```

Use `python -m pytest` rather than plain `pytest`: running it through `python -m` adds the project folder to Python's import path so the tests can import `pawpal_system`.

### What the tests cover

All tests are in `tests/test_pawpal.py` and use a fixed date, so results don't depend on the day you run them.

- **Task management and input validation:** marking tasks complete, adding tasks to pets, updating only the fields you pass, and rejecting bad values (zero/negative durations, unknown priorities or frequencies, invalid `"HH:MM"` times, tasks that run past midnight, negative available time).
- **Sorting by time and priority:** clock order with untimed tasks last, original order kept for identical times, and high → medium → low priority with shorter tasks first on ties.
- **Filtering:** by pet name, by completion status, and both together, including no-match and no-filter cases.
- **Scheduling within available time:** the plan never exceeds the owner's time, exact fits are accepted, oversized tasks are skipped while smaller ones still fit, and regenerating replaces the old plan.
- **Daily and weekly recurring tasks:** next occurrences 1 or 7 days later, `once` tasks not repeating, completed tasks kept as history, future tasks left out, and overdue tasks carried over.
- **Conflict detection and warnings:** overlapping and identical start times, touching endpoints not counted, conflicts across pets, multiple overlapping pairs, and the exact warning text (including a `24:00` end time).
- **Edge cases:** empty schedules (no pets or no tasks), a pet with no tasks, zero available time, invalid inputs, and completing the same task twice without creating duplicates.

Sample test output (from `python -m pytest`):

```text
============================= test session starts =============================
platform win32 -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\USER\ai110-module2show-pawpal
plugins: anyio-4.15.1
collected 78 items

tests\test_pawpal.py ................................................... [ 65%]
...........................                                              [100%]

============================= 78 passed in 0.06s ==============================
```

### Confidence Level

**Confidence Level: 4/5 stars (★★★★☆)**

The 78 passing tests give strong confidence in the core scheduling logic: priorities, time limits, sorting, filtering, recurrence, and conflict detection are all checked, including the main edge cases. It is not 5/5 because the Streamlit interface in `app.py` is not covered by the pytest suite and has not been tested thoroughly in a real browser, and there is no performance testing with large numbers of pets and tasks.

## 📐 Smarter Scheduling

The core plan comes from `Scheduler.generate_schedule()`. It goes through tasks from **high → medium → low** priority (shorter tasks first when priorities are equal) and adds each one that still fits in the owner's available time. Four extra features build on top of it.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Clock order by `"HH:MM"` start time; untimed tasks last |
| Filtering | `Scheduler.filter_tasks()` | By pet name, completion status, or both |
| Conflict handling | `Scheduler.detect_conflicts()`, `Scheduler.format_conflict()` | Finds overlapping time slots and prints warnings |
| Recurring tasks | `Task.next_occurrence()`, `Pet.complete_task()` | `once`, `daily`, or `weekly`; next copy created on completion |

### 1. Sorting by Time

`Scheduler.sort_by_time(tasks=None)` returns tasks in clock order, earliest first.

- Each task can have an optional `start_time` in 24-hour `"HH:MM"` format, such as `"08:30"` or `"14:00"`.
- Tasks without a start time can happen at any time, so they appear **last**.
- With no argument it sorts today's `daily_plan`; you can also pass in any list of tasks. The original list is not changed.
- Sorting by time only changes the **display order**. *Which* tasks make it into the plan is still decided by priority.

### 2. Filtering Tasks

`Scheduler.filter_tasks(pet_name=None, completed=None)` returns only the tasks you ask for.

- `filter_tasks(pet_name="Rex")` → only Rex's tasks.
- `filter_tasks(completed=False)` → only tasks that still need doing.
- Both filters can be **combined**: `filter_tasks(pet_name="Rex", completed=False)` → Rex's unfinished tasks.
- Leaving an argument as `None` means "don't filter on this". No arguments returns every task; no matches returns an empty list.

### 3. Conflict Detection

`Scheduler.detect_conflicts(tasks=None)` finds tasks whose time ranges overlap, and `Scheduler.format_conflict()` turns each one into a readable warning:

```text
WARNING: Walk (Rex) 08:00-08:30 overlaps with Feed (Mia) 08:15-08:25.
```

- Each task's time range is its start time to start time + duration.
- Every pair of timed tasks is compared (using `itertools.combinations`). Two tasks overlap when **each one starts before the other ends**.
- Tasks that only touch, like one ending at 08:30 and the next starting at 08:30, are **not** a conflict.
- Conflicts are checked across all pets, because one owner can't do two things at once. Tasks without a start time are ignored.
- Conflicts only produce **warnings**. Tasks are never removed or rescheduled automatically; the owner decides what to change.

### 4. Recurring Tasks

Each task has a `frequency` and a `due_date` (today by default):

| Frequency | What happens when it's completed |
|-----------|----------------------------------|
| `once` | Nothing else is created |
| `daily` | A new copy is due **1 day** later |
| `weekly` | A new copy is due **7 days** later |

- `Task.next_occurrence()` builds the next copy, with the same details, `completed=False`, and the new due date. It does not change the original task.
- `Pet.complete_task(task)` marks the task done and adds its next occurrence to the pet's task list.
- The completed task **stays in the list as history**, so you can see what was done.
- Calling `complete_task()` on a task that is already completed does nothing, so **duplicate occurrences are prevented**.
- `generate_schedule(for_date=None)` only plans tasks that are due on or before the chosen day (default: today). Future tasks and old completed tasks are left out, and overdue unfinished tasks are carried over.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
