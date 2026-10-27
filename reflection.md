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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

For conflict detection, I originally used nested loops to compare every pair of scheduled tasks. After reviewing the algorithm with AI, I changed it to use itertools.combinations() because it makes the code shorter and easier to understand.

Both approaches have O(n²) time complexity, but combinations() improves readability while keeping the same behavior. I also added a helper function, _time_range(), to avoid repeating time calculations.

A sorting-based algorithm could be faster for larger schedules, but it would add complexity. Since PawPal+ only handles a small number of daily tasks, I decided to prioritize readability and correctness over performance. All 40 tests still passed after the change.

To put O(n²) in perspective: checking every pair of n tasks takes n × (n − 1) ÷ 2 comparisons, so 10 tasks need only 45 comparisons and even 100 tasks need 4,950, which is still instant. The sorting-based version would sort tasks by start time and stop checking as soon as the next task starts after the current one ends. That is faster for very large lists, but it is easy to get wrong: comparing each task only with its neighbour misses cases like an 08:00–10:00 walk overlapping a 09:00 task when an 08:30 task sits between them. It would also return conflict pairs in clock order instead of list order, which would change my existing behavior and tests. The nested-loop and combinations() versions check every pair, so they are correct without any extra reasoning, and combinations() states that intent directly in one line.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
