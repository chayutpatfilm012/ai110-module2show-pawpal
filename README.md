# 🐾 PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a busy pet owner plan daily care tasks for their pets. You add your pets and their tasks, tell PawPal+ how much time you have today, and it builds a plan: the most important tasks first, shown in time order, with warnings when two tasks overlap.

The scheduling logic lives in plain Python classes (`Owner`, `Pet`, `Task`, `Scheduler`) and is covered by 78 automated tests. A command-line demo (`main.py`) shows the same logic without the UI.

> **Note:** PawPal+ keeps your pets and tasks in Streamlit's session state. Data lasts while the browser tab is open, but it is **not saved permanently**. Refreshing the page or restarting the app starts fresh.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

The system was designed first (UML), then implemented in Python, then connected to the Streamlit UI.

## Features

1. **Manage multiple pets:** add pets with a name, species (dog, cat, other), and age. Duplicate or empty pet names are rejected.
2. **Add pet care tasks:** each task has a title, duration (1–240 minutes), priority (low, medium, high), frequency (once, daily, weekly), and an optional 24-hour start time such as `08:30`. Invalid times, or tasks that would run past midnight, show an error instead of crashing the app.
3. **Generate a daily schedule:** PawPal+ picks tasks by priority (shorter tasks first on ties) until your available time runs out.
4. **Sort by start time:** the schedule and task list are displayed in clock order; tasks without a start time show as **Anytime** and appear last.
5. **Filter tasks:** view tasks for one pet or all pets, and show All, Pending, or Completed tasks.
6. **Complete tasks with automatic recurrence:** marking a daily or weekly task complete creates its next occurrence (1 or 7 days later). A task can't be completed twice.
7. **Detect scheduling conflicts:** overlapping start times are shown as warnings. Tasks are never moved or removed automatically.
8. **See scheduled, skipped, and completed tasks:** the schedule shows what was planned, a Skipped table explains what was left out and why, and the task list keeps completed tasks as history. A "Why this plan?" section gives a text summary.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

### Run the command-line demo

```bash
python main.py
```

### Development workflow

PawPal+ was built in these steps:

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Project structure

| File | What it contains |
|------|------------------|
| `app.py` | The Streamlit user interface |
| `pawpal_system.py` | The `Owner`, `Pet`, `Task`, and `Scheduler` classes |
| `main.py` | Command-line demo of every scheduling feature |
| `tests/test_pawpal.py` | 78 pytest tests |
| [diagrams/uml_final.mmd](diagrams/uml_final.mmd) | Final UML class diagram (architecture) |
| [diagrams/uml.mmd](diagrams/uml.mmd) | Working UML diagram used during development |
| `reflection.md` | Project reflection |

## Demo Walkthrough

### A. Main UI features

Run `streamlit run app.py`. The page has these sections, from top to bottom:

| Section | What you can do |
|---------|-----------------|
| **Owner** | Enter the owner's name and today's available time in minutes. |
| **Pets** | Enter a pet's name, species, and age, then click **Add pet**. Your pets appear in a table with their task counts. |
| **Tasks** | Choose a pet, enter a task title, duration, priority, frequency, and optional start time, then click **Add task**. |
| **Mark a task complete** | Pick a pending task from the dropdown and click **Mark complete**. Daily and weekly tasks get their next occurrence automatically. |
| **Task list** | Filter with **Show pet** (All Pets or one pet) and **Show status** (All, Pending, Completed). Tasks are listed in time order. |
| **Build Schedule** | Click **Generate schedule** to see Today's Schedule, any time conflict warnings, the Skipped table, and a "Why this plan?" summary. |

### B. Example workflow

1. **Launch the app** with `streamlit run app.py`.
2. **Enter the owner:** set the owner name to `Sam` and available time to `60` minutes.
3. **Add two pets:** Rex (dog, 3) and Mia (cat, 2). Each shows a message such as *"Added Rex the dog."*
4. **Create tasks:**

   | Pet | Task | Duration | Priority | Frequency | Start time |
   |-----|------|----------|----------|-----------|------------|
   | Rex | Walk | 30 | high | daily | 08:00 |
   | Mia | Feed | 10 | high | daily | 08:15 |
   | Rex | Play | 20 | medium | weekly | 17:30 |
   | Mia | Groom | 15 | low | once | *(blank)* |

5. **View and filter tasks:** in the Task list, set **Show pet** to `Mia`. Only Feed (08:15) and Groom (Anytime) are listed.
6. **Generate today's schedule:** click **Generate schedule**. You'll see *"Scheduled 3 task(s) using 60 of 60 minutes."*
7. **Observe priority selection and time order:** the two high-priority tasks (Feed, then Walk, because shorter goes first) and the medium-priority Play fill exactly 60 minutes. Groom (low) is in the Skipped table with the reason *"not enough time left"*. Today's Schedule then lists the chosen tasks by clock time: **08:00 Walk, 08:15 Feed, 17:30 Play**.
8. **Complete a recurring task:** under **Mark a task complete**, choose `Rex: Walk (08:00, due …)` and click **Mark complete**. You'll see *"Completed 'Walk' for Rex. Next daily occurrence is due …"* with tomorrow's date. The task list now shows the completed Walk (with the Completed filter) and a new pending Walk due tomorrow.
9. **View conflict warnings:** in step 6, Walk (08:00–08:30) and Feed (08:15–08:25) overlap, so the schedule shows:

   > WARNING: Feed (Mia) 08:15-08:25 overlaps with Walk (Rex) 08:00-08:30.

   followed by a note that conflicts are warnings only. Both tasks stay in the plan, and you decide whether to change a start time. If you click **Generate schedule** again after step 8, the warning is gone: today's Walk is already completed, so it moves to the Skipped table with the reason *"already completed"*.

### C. Key scheduler behaviors

- **Priority-based selection:** tasks are considered high → medium → low, shorter first on ties, and each one is added if it still fits in the available time.
- **Sorting by time for display:** the chosen tasks are *shown* in clock order, but sorting never changes *which* tasks were chosen.
- **Filtering:** by pet, by completion status, or both.
- **Daily and weekly recurrence:** completing a task creates the next copy 1 day (daily) or 7 days (weekly) later; `once` tasks don't repeat. Completed tasks stay in the list as history.
- **Overlapping task warnings:** any two scheduled tasks whose times overlap produce a warning. **Conflicts never move or remove tasks automatically.**
- **Limited time:** tasks that don't fit in the remaining time are skipped with the reason *"not enough time left"*, while smaller tasks later in the list can still fit.

See [Smarter Scheduling](#-smarter-scheduling) below for how each of these works.

### D. CLI sample output

`python main.py` runs the same logic without the UI. It prints today's schedule, then demonstrates sorting, filtering, recurrence, and conflict detection. Actual output (recurring task dates depend on the day you run it; this run was on 2026-10-27):

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

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

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
