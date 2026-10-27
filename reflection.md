# PawPal+ Project Reflection

## 1. System Design

The three core actions of the PawPal+ application are:

1. **Add a Pet:** Users can add a new pet and store basic information such as its name, age, and type.

2. **Schedule a Task:** Users can create tasks for their pets, such as feeding, walking, or grooming, and set a scheduled time.

3. **View Daily Tasks:** Users can view all scheduled tasks for the day to help them manage their pets' daily activities.

**a. Initial design**

I designed the PawPal+ system using four main classes: Owner, Pet, Task, and Scheduler.

- **Owner:** Stores the owner's information, available time, preferences, and pets.
- **Pet:** Stores pet information and manages tasks related to each pet.
- **Task:** Represents activities such as feeding, walking, and grooming. Each task has a duration, priority, and completion status.
- **Scheduler:** Organizes tasks based on priority and available time to create a daily schedule.

I chose these classes because each one has a clear responsibility. This makes the system easier to understand, maintain, and improve.

**b. Design changes**

After reviewing my design with AI, I made three improvements.

First, I connected the Scheduler to the Owner so it can access available time and pet tasks without storing duplicate data.

Second, I added pet_name to the Task class to identify which pet each task belongs to.

Finally, I decided to keep priority as a string and use a priority mapping during scheduling to make sure tasks are sorted correctly.

These changes make the design simpler and easier to maintain.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

My scheduler considers four constraints:

1. **Available time:** the owner's available minutes are a hard limit. The total duration of the daily plan can never go over it.
2. **Priority:** tasks are considered in high → medium → low order, and shorter tasks go first when two tasks have the same priority.
3. **Due date and completion status:** only unfinished tasks that are due today or overdue are scheduled. Future tasks and old completed tasks are left out.
4. **Start time:** start times do not decide which tasks are chosen, but they are used to show the plan in time order and to warn about overlapping tasks.

I decided that available time mattered most because it is the one rule a real owner cannot break: if they only have 60 minutes, a 75-minute plan is useless. Priority came second because the most important care, like feeding and walks, should be protected when time runs out. I deliberately kept start times out of the selection step, so a conflict is reported as a warning instead of silently dropping an important task. The Owner class also stores preferences, but the scheduler does not use them yet, so I treat them as a future improvement rather than a current constraint.

**b. Tradeoffs**

For conflict detection, I originally used nested loops to compare every pair of scheduled tasks. After reviewing the algorithm with AI, I changed it to use itertools.combinations() because it makes the code shorter and easier to understand.

Both approaches have O(n²) time complexity, but combinations() improves readability while keeping the same behavior. I also added a helper function, _time_range(), to avoid repeating time calculations.

A sorting-based algorithm could be faster for larger schedules, but it would add complexity. Since PawPal+ only handles a small number of daily tasks, I decided to prioritize readability and correctness over performance. All 40 tests still passed after the change.

To put O(n²) in perspective: checking every pair of n tasks takes n × (n − 1) ÷ 2 comparisons, so 10 tasks need only 45 comparisons and even 100 tasks need 4,950, which is still instant. The sorting-based version would sort tasks by start time and stop checking as soon as the next task starts after the current one ends. That is faster for very large lists, but it is easy to get wrong: comparing each task only with its neighbour misses cases like an 08:00–10:00 walk overlapping a 09:00 task when an 08:30 task sits between them. It would also return conflict pairs in clock order instead of list order, which would change my existing behavior and tests. The nested-loop and combinations() versions check every pair, so they are correct without any extra reasoning, and combinations() states that intent directly in one line.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code in VS Code for the whole project: drafting the UML, turning it into class skeletons, implementing the scheduler, connecting it to Streamlit, writing tests, and updating the documentation.

**Most effective features.** Three features helped the most when building the scheduler:

- **Agent Mode** could read my existing files, edit several of them in one step, and keep them consistent. For example, when I added recurring tasks, it updated `pawpal_system.py`, `main.py`, `tests/test_pawpal.py`, and the UML together.
- **AI code review** found architectural problems I had missed. When I asked it to review my first class skeleton, it pointed out that the Scheduler stored its own copy of `available_time` and its own task list, which could easily get out of sync with the Owner, and that sorting priority strings alphabetically puts "high" < "low" < "medium". These findings led directly to the design changes in section 1b.
- **Automated pytest runs** let me check every change immediately. The AI ran `python -m pytest` and `python main.py` after each step and reported the real output, so I could see straight away whether something broke.

The most helpful prompts were ones that separated planning from coding. I often asked for a plan first ("Do not modify any files yet"), reviewed it, made my own decisions, and only then asked for the implementation. I also got better results when I listed exact requirements and constraints, such as "keep the existing constructors working", "do not change the scheduling logic", and "do not invent output".

**Separate chat sessions.** I used separate chats for planning, implementation, and testing. This kept each conversation focused on one kind of work. In a planning chat, the AI was not tempted to start editing files; in an implementation chat, I could point it to an approved plan instead of re-explaining every decision; and in a testing chat, I could focus on edge cases without design discussions getting mixed in. It also gave me natural checkpoints to review and commit my work before moving to the next phase.

**b. Judgment and verification**

The clearest example of a suggestion I did not accept as-is was conflict detection. When I asked the AI how my nested-loop `detect_conflicts()` could be simplified, it described two options: rewriting the loops with `itertools.combinations()`, or a faster sorting-based algorithm that sorts tasks by start time and stops checking early. The sorting-based version was faster on paper, but I rejected it. It was harder to read, it is easy to get subtly wrong, and it would have changed the order of the returned conflict pairs, which would break my existing behavior and tests. I chose `combinations()` because it keeps the same O(n²) behavior while making the intent ("check every pair") obvious, and PawPal+ only ever handles a small number of daily tasks.

I also made my own decisions on smaller design points. For example, the AI suggested either storing priority as a number or keeping it as a string with a mapping, and I chose to keep readable strings ("low", "medium", "high") with a mapping used only for sorting. I also decided that conflicts should only produce warnings rather than having the app remove or reschedule tasks automatically.

To verify AI suggestions, I relied on evidence rather than trust:

- I ran `python -m pytest` after every change. The suite grew from 2 tests to 78, and every refactor had to keep all existing tests passing.
- For the `combinations()` refactor, the `main.py` output was compared before and after the change and was identical, which showed the behavior had not changed.
- For the Streamlit UI, the app was driven with Streamlit's AppTest to check that adding pets, adding tasks, filtering, completing recurring tasks, and conflict warnings really worked.
- For the final UML, the diagram was checked with the Mermaid parser and compared against the actual Python classes, so the diagram and code match.

---

## 4. Testing and Verification

**a. What you tested**

My final test suite has 78 passing pytest cases in `tests/test_pawpal.py`. They cover:

- **Task management and validation:** marking tasks complete, adding tasks to pets, partial updates, and rejecting invalid input such as zero or negative durations, unknown priorities or frequencies, bad `"HH:MM"` times, tasks that end after midnight, and negative available time.
- **Priority-based scheduling:** high → medium → low order with shorter tasks first, never going over the available time, exact fits, zero available time, and an oversized task being skipped while smaller tasks still fit.
- **Sorting and filtering:** time order with untimed tasks last, identical start times keeping their original order, and filtering by pet, completion status, or both.
- **Recurring tasks:** daily and weekly next occurrences, `once` tasks not repeating, completed tasks staying in history, future tasks being excluded, overdue tasks being carried over, and completing the same task twice not creating duplicates.
- **Conflict detection:** overlapping and identical start times, tasks that only touch not counting as conflicts, conflicts between different pets, multiple overlapping pairs, and the exact warning text, including a task that ends at `24:00`.

These tests were important because the scheduler makes decisions that are easy to get slightly wrong, like off-by-one comparisons at the edge of the time limit or at the end of a task. I used a fixed date in the tests so recurring-task results do not depend on the day the tests are run. The tests also protected me during refactoring: when I changed conflict detection to use `combinations()`, the passing tests showed that the behavior was the same.

**b. Confidence**

I would rate my confidence at 4 out of 5. The core scheduling logic is well tested, including the main edge cases, and the command-line demo matches the expected results. It is not 5 out of 5 because the Streamlit interface is not part of the pytest suite and has only been checked with AppTest rather than thoroughly in a real browser, and I have not tested performance with large numbers of pets and tasks.

If I had more time, I would test:

- The Streamlit UI in a real browser, including narrow screens and many tasks.
- Larger inputs, such as hundreds of tasks, to measure how the O(n²) conflict check performs.
- Two pets with the same name created directly through the backend, since the app blocks duplicate names but `Owner.add_pet()` does not.
- What happens if the app stays open past midnight, since "today" is calculated when the schedule is generated.

---

## 5. Reflection

**a. What went well**

I am most satisfied with how cleanly the logic and the UI are separated. All of the scheduling rules live in `pawpal_system.py`, and both the Streamlit app and `main.py` use the same methods instead of duplicating logic. Because of that, I could test the important behavior with pytest without needing the UI, and adding a new feature like recurring tasks only had to be done once.

I am also happy that the project grew in small, safe steps. Each phase (sorting and filtering, recurring tasks, conflict detection, UI integration) kept the earlier demo output and tests working, so I always had a working version.

**b. What you would improve**

If I had another iteration, I would:

- **Use owner preferences in scheduling.** The Owner stores preferences, but the scheduler ignores them. For example, a preference for morning walks could influence which tasks are chosen or suggested.
- **Save data permanently.** The app uses Streamlit session state, so all pets and tasks disappear when the page is refreshed. Saving to a JSON file or a small database would make the app usable day to day.
- **Rethink overdue recurring tasks.** Right now, the next occurrence of an overdue daily task is based on its old due date, so a task that is three days overdue creates a copy that is still overdue. Basing it on the completion date might be more useful.
- **Help resolve conflicts.** The app only warns about overlapping tasks. A future version could suggest a free time slot while still leaving the final decision to the owner.

**c. Key takeaway**

The most important thing I learned is what it means to be the lead architect when working with AI. The AI could write code, tests, and documentation very quickly, but it could not decide what the system should be. Those decisions were mine: connecting the Scheduler to the Owner instead of copying data, keeping priority as a readable string, showing conflicts as warnings instead of removing tasks, and choosing `combinations()` over a faster but more complicated algorithm.

I learned to evaluate suggestions instead of accepting them automatically. A suggestion can be technically correct and still be the wrong choice for the project. For PawPal+, readability and correctness mattered more than performance, because a small, easy-to-check algorithm is better than a faster one I cannot easily trust.

I also learned that I am responsible for keeping the whole design consistent. I made sure the UML diagram matched the Python classes at each stage and created a final diagram that was checked against the real code. Most importantly, I verified AI-generated work with tests and real program output rather than trusting explanations. In the end, the AI was a fast and helpful collaborator, but I am responsible for the final design and for being able to explain every decision in it.
