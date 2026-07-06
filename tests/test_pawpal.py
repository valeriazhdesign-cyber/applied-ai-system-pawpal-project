from pawpal_system import Category, Pet, Priority, Task


def make_task(**kwargs):
    defaults = dict(
        name="Morning Walk",
        category=Category.WALK,
        duration=30,
        priority=Priority.HIGH,
    )
    defaults.update(kwargs)
    return Task(**defaults)


def test_mark_complete_sets_completed_true():
    task = make_task()
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_mark_complete_is_idempotent():
    task = make_task()
    task.mark_complete()
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Rex", species="dog")
    assert len(pet.tasks) == 0
    pet.add_task(make_task())
    assert len(pet.tasks) == 1
    pet.add_task(make_task(name="Dinner"))
    assert len(pet.tasks) == 2
