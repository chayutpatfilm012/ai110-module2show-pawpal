import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to PawPal+, a pet care planning assistant.

Add your pets and their care tasks, then generate a daily plan that fits the time you have.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

with st.expander("How the schedule is built", expanded=True):
    st.markdown(
        """
- Tasks are ordered by priority: **high**, then **medium**, then **low**
- Tasks with the same priority go shortest first
- Completed tasks and tasks not due yet are skipped
- Tasks are added until the owner's available time runs out
- The chosen tasks are then shown in time order, and overlapping times are flagged as warnings
- Completing a daily or weekly task automatically adds its next occurrence
"""
    )

# Create the Owner only once. Streamlit reruns this whole file after every click,
# so the Owner (and its pets and tasks) must live in session_state to be kept.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_time=60)

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)


def show_message_after_rerun(text: str) -> None:
    """Save a success message, then rerun so every table shows the updated data."""
    st.session_state.message = text
    st.rerun()


def task_row(task: Task) -> dict:
    """Return one table row describing a task."""
    return {
        "Start time": task.start_time or "Anytime",
        "Pet": task.pet_name,
        "Task": task.title,
        "Duration (min)": task.duration_minutes,
        "Priority": task.priority,
        "Frequency": task.frequency,
        "Due": str(task.due_date),
        "Status": "Completed" if task.completed else "Pending",
    }


def find_pet_for(task: Task) -> Pet:
    """Return the pet that owns this exact task object."""
    return next(pet for pet in owner.pets if any(existing is task for existing in pet.tasks))


st.divider()

st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value="Jordan")
with col2:
    available_time = st.number_input(
        "Available time today (minutes)", min_value=0, max_value=1440, value=60
    )
try:
    owner.set_available_time(int(available_time))
except ValueError as error:
    st.error(f"Could not set available time: {error}")

st.markdown("### Pets")

col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    age = st.number_input("Age (years)", min_value=0, max_value=50, value=2)

if st.button("Add pet"):
    name = pet_name.strip()
    existing_names = [pet.name.lower() for pet in owner.pets]
    if not name:
        st.error("Please enter a pet name.")
    elif name.lower() in existing_names:
        st.error(f"You already have a pet named {name}.")
    else:
        owner.add_pet(Pet(name, species, int(age)))
        st.success(f"Added {name} the {species}.")

if owner.pets:
    st.write("Your pets:")
    st.table(
        [
            {"Name": pet.name, "Species": pet.species, "Age": pet.age, "Tasks": len(pet.tasks)}
            for pet in owner.pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")
st.caption("Choose a pet, then add a care task for it.")

if "message" in st.session_state:
    st.success(st.session_state.pop("message"))

if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    pet_names = [pet.name for pet in owner.pets]
    selected_pet_name = st.selectbox("Pet", pet_names)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
    start_time = st.text_input(
        "Start time (optional, 24-hour HH:MM)",
        value="",
        placeholder="e.g. 08:30 — leave blank for any time",
        key="start_time",
    )

    if st.button("Add task"):
        title = task_title.strip()
        if not title:
            st.error("Please enter a task title.")
        else:
            try:
                task = Task(title, int(duration), priority, frequency, start_time=start_time.strip())
            except ValueError as error:
                st.error(f"Could not add task: {error}")
            else:
                selected_pet = next(pet for pet in owner.pets if pet.name == selected_pet_name)
                selected_pet.add_task(task)
                show_message_after_rerun(f"Added '{title}' for {selected_pet.name}.")

all_tasks = owner.get_all_tasks()

if all_tasks:
    st.markdown("#### Mark a task complete")
    pending_tasks = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
    if not pending_tasks:
        st.info("All tasks are completed.")
    else:
        # Options are list positions, so two tasks with the same title are still told apart.
        task_number = st.selectbox(
            "Pending task",
            range(len(pending_tasks)),
            format_func=lambda i: (
                f"{pending_tasks[i].pet_name}: {pending_tasks[i].title} "
                f"({pending_tasks[i].start_time or 'Anytime'}, due {pending_tasks[i].due_date})"
            ),
            key="task_to_complete",
        )
        if st.button("Mark complete", key="mark_complete"):
            task = pending_tasks[task_number]
            next_task = find_pet_for(task).complete_task(task)
            if next_task is not None:
                show_message_after_rerun(
                    f"Completed '{task.title}' for {task.pet_name}. "
                    f"Next {task.frequency} occurrence is due {next_task.due_date}."
                )
            elif task.completed:
                show_message_after_rerun(f"Completed '{task.title}' for {task.pet_name}.")
            else:
                st.error(f"'{task.title}' could not be completed.")

    st.markdown("#### Task list")
    col1, col2 = st.columns(2)
    with col1:
        pet_filter = st.selectbox(
            "Show pet", ["All Pets"] + [pet.name for pet in owner.pets], key="pet_filter"
        )
    with col2:
        status_filter = st.selectbox(
            "Show status", ["All", "Pending", "Completed"], key="status_filter"
        )

    filtered_tasks = scheduler.filter_tasks(
        pet_name=None if pet_filter == "All Pets" else pet_filter,
        completed={"All": None, "Pending": False, "Completed": True}[status_filter],
    )
    if filtered_tasks:
        st.table([task_row(task) for task in scheduler.sort_by_time(filtered_tasks)])
    else:
        st.info("No tasks match these filters.")
elif owner.pets:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption(
    "Creates today's plan from all of your pets' tasks. Tasks are chosen by priority, "
    "then shown in time order."
)

if st.button("Generate schedule"):
    if not all_tasks:
        st.warning("There are no tasks to schedule yet. Add a pet and some tasks first.")
    else:
        plan = scheduler.generate_schedule()
        total = sum(task.duration_minutes for task in plan)

        st.success(
            f"Scheduled {len(plan)} task(s) using {total} of {owner.available_time} minutes."
        )

        if plan:
            st.markdown("#### Today's Schedule")
            st.table(
                [
                    {
                        "Start time": task.start_time or "Anytime",
                        "Pet": task.pet_name,
                        "Task": task.title,
                        "Duration (min)": task.duration_minutes,
                        "Priority": task.priority,
                        "Status": "Completed" if task.completed else "Pending",
                    }
                    for task in scheduler.sort_by_time()
                ]
            )

            conflicts = scheduler.detect_conflicts()
            if conflicts:
                st.markdown("#### Time Conflicts")
                for task_a, task_b in conflicts:
                    st.warning(scheduler.format_conflict(task_a, task_b))
                st.info(
                    "Conflicts are warnings only. PawPal+ does not move or remove tasks, "
                    "so adjust the start times yourself if needed."
                )
            else:
                st.info("No time conflicts in today's plan.")
        else:
            st.warning("No tasks fit in the available time.")

        if scheduler.skipped:
            st.markdown("#### Skipped")
            st.table(
                [
                    {
                        "Pet": task.pet_name,
                        "Task": task.title,
                        "Duration (min)": task.duration_minutes,
                        "Priority": task.priority,
                        "Reason": scheduler.get_skip_reason(task),
                    }
                    for task in scheduler.skipped
                ]
            )

        with st.expander("Why this plan?"):
            st.text(scheduler.explain_schedule())
