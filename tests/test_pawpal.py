from pawpal_system import Pet, Task


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
