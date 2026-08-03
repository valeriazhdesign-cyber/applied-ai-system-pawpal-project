from pawpal_system import CareGuidanceRetriever, Category, Owner, Pet, Priority, Scheduler, Task


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


def make_owner(minutes: int = 120) -> Owner:
    owner = Owner("Alex", available_minutes=minutes)
    return owner


def make_scheduler(owner: Owner, start_time: str = "08:00") -> Scheduler:
    return Scheduler(owner, start_time=start_time)


def test_add_task_increases_pet_task_count():
    pet = Pet("Rex", species="dog")
    assert len(pet.tasks) == 0
    pet.add_task(make_task())
    assert len(pet.tasks) == 1
    pet.add_task(make_task(name="Dinner"))
    assert len(pet.tasks) == 2


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """Tasks with preferred_time should come out earliest-first."""
    scheduler = make_scheduler(make_owner())
    t1 = make_task(name="Dinner",    preferred_time="18:00")
    t2 = make_task(name="Lunch",     preferred_time="12:00")
    t3 = make_task(name="Breakfast", preferred_time="08:00")

    result = scheduler.sort_by_time([t1, t2, t3])

    assert [t.name for t in result] == ["Breakfast", "Lunch", "Dinner"]


def test_sort_by_time_tasks_without_preferred_time_sort_last():
    """Tasks with no preferred_time should appear after all timed tasks."""
    scheduler = make_scheduler(make_owner())
    timed   = make_task(name="Walk",   preferred_time="07:00")
    untimed = make_task(name="Groom",  preferred_time=None)

    result = scheduler.sort_by_time([untimed, timed])

    assert result[0].name == "Walk"
    assert result[1].name == "Groom"


def test_sort_by_priority_highest_first():
    """sort_by_priority should put HIGH before MEDIUM before LOW."""
    scheduler = make_scheduler(make_owner())
    low  = make_task(name="Low",  priority=Priority.LOW)
    med  = make_task(name="Med",  priority=Priority.MEDIUM)
    high = make_task(name="High", priority=Priority.HIGH)

    result = scheduler.sort_by_priority([low, med, high])

    assert [t.name for t in result] == ["High", "Med", "Low"]


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_complete_daily_task_queues_next_occurrence():
    """Completing a daily task should append a fresh, pending copy."""
    pet  = Pet("Mochi", species="cat")
    task = make_task(name="Feed", recurring="daily")
    pet.add_task(task)

    pet.complete_task(task, today="2026-07-06")

    assert task.completed is True
    assert task.last_done == "2026-07-06"
    assert len(pet.tasks) == 2
    next_task = pet.tasks[1]
    assert next_task.completed is False
    assert next_task.name == "Feed"


def test_daily_task_done_today_is_not_due():
    """A daily task completed today should be filtered out for today."""
    task = make_task(recurring="daily", last_done="2026-07-06")
    assert task.is_due("2026-07-06") is False


def test_daily_task_done_yesterday_is_due():
    """A daily task completed yesterday should appear in today's schedule."""
    task = make_task(recurring="daily", last_done="2026-07-05")
    assert task.is_due("2026-07-06") is True


def test_weekly_task_exactly_seven_days_ago_is_due():
    """Boundary: weekly task done exactly 7 days ago is due (≥7 triggers True)."""
    task = make_task(recurring="weekly", last_done="2026-06-29")
    assert task.is_due("2026-07-06") is True


def test_weekly_task_done_three_days_ago_is_not_due():
    """A weekly task completed 3 days ago is not yet due."""
    task = make_task(recurring="weekly", last_done="2026-07-03")
    assert task.is_due("2026-07-06") is False


def test_non_recurring_task_complete_does_not_queue_next():
    """Completing a non-recurring task must not add anything to pet.tasks."""
    pet  = Pet("Buddy", species="dog")
    task = make_task(name="Vet Visit", recurring=None)
    pet.add_task(task)

    result = pet.complete_task(task)

    assert result is None
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_overlapping_tasks():
    """Two tasks whose time windows overlap should produce a warning."""
    owner     = make_owner()
    scheduler = make_scheduler(owner)
    t1 = make_task(name="Walk",  preferred_time="08:00", duration=30)  # 08:00–08:30
    t2 = make_task(name="Groom", preferred_time="08:15", duration=30)  # 08:15–08:45

    warnings = scheduler.detect_conflicts([t1, t2])

    assert len(warnings) == 1
    assert "Walk" in warnings[0]
    assert "Groom" in warnings[0]


def test_detect_conflicts_no_warning_for_back_to_back_tasks():
    """Tasks that share an endpoint but do not overlap should not be flagged."""
    owner     = make_owner()
    scheduler = make_scheduler(owner)
    t1 = make_task(name="Walk",  preferred_time="08:00", duration=30)  # ends 08:30
    t2 = make_task(name="Groom", preferred_time="08:30", duration=30)  # starts 08:30

    warnings = scheduler.detect_conflicts([t1, t2])

    assert warnings == []


def test_detect_conflicts_no_warning_for_non_overlapping_tasks():
    """Tasks with a gap between them should not produce any conflict warning."""
    owner     = make_owner()
    scheduler = make_scheduler(owner)
    t1 = make_task(name="Walk",  preferred_time="08:00", duration=20)  # ends 08:20
    t2 = make_task(name="Groom", preferred_time="09:00", duration=20)  # starts 09:00

    warnings = scheduler.detect_conflicts([t1, t2])

    assert warnings == []


def test_handle_conflicts_keeps_higher_priority_task():
    """When two tasks overlap, handle_conflicts should drop the lower-priority one."""
    owner     = make_owner()
    scheduler = make_scheduler(owner)
    high = make_task(name="Walk",  priority=Priority.HIGH,   preferred_time="08:00", duration=60)
    low  = make_task(name="Groom", priority=Priority.LOW,    preferred_time="08:30", duration=30)

    # sort_by_priority first (generate_plan does this before handle_conflicts)
    sorted_tasks = scheduler.sort_by_priority([low, high])
    result = scheduler.handle_conflicts(sorted_tasks)

    names = [t.name for t in result]
    assert "Walk" in names
    assert "Groom" not in names


# ---------------------------------------------------------------------------
# Care guidance retrieval
# ---------------------------------------------------------------------------

def test_retrieve_returns_guidance_for_matching_category():
    """A meds task in the task list should surface the meds guidance snippet."""
    retriever = CareGuidanceRetriever()
    owner = make_owner()
    meds_task = make_task(name="Flea Medication", category=Category.MEDS)

    guidance = retriever.retrieve([meds_task], owner)

    assert any("Medication" in g for g in guidance)


def test_retrieve_returns_no_guidance_for_empty_task_list():
    """With no tasks and no matching preferences, retrieve should return nothing."""
    retriever = CareGuidanceRetriever()
    owner = make_owner()

    assert retriever.retrieve([], owner) == []


def test_retrieve_respects_top_k_limit():
    """retrieve should never return more than top_k snippets even with many matches."""
    retriever = CareGuidanceRetriever()
    owner = make_owner()
    tasks = [
        make_task(name="Meds", category=Category.MEDS),
        make_task(name="Feed", category=Category.FEEDING),
        make_task(name="Walk", category=Category.WALK),
    ]

    guidance = retriever.retrieve(tasks, owner, top_k=2)

    assert len(guidance) == 2


def test_build_rationale_appends_guidance_to_base_explanation():
    """build_rationale should append retrieved guidance beneath the base explanation."""
    retriever = CareGuidanceRetriever()
    owner = make_owner()
    meds_task = make_task(name="Flea Medication", category=Category.MEDS)

    rationale = retriever.build_rationale("Scheduled 1 task(s).", [meds_task], owner)

    assert rationale.startswith("Scheduled 1 task(s).")
    assert "Medication" in rationale


def test_build_rationale_returns_base_explanation_unchanged_when_no_guidance_matches():
    """With no matching tasks or preferences, build_rationale should not alter the base text."""
    retriever = CareGuidanceRetriever()
    owner = make_owner()

    rationale = retriever.build_rationale("Scheduled 0 task(s).", [], owner)

    assert rationale == "Scheduled 0 task(s)."


def test_generate_plan_explanation_includes_retrieved_guidance():
    """generate_plan should fold guidance for the scheduled tasks into plan.explanation."""
    owner = make_owner()
    scheduler = make_scheduler(owner)
    meds_task = make_task(name="Flea Medication", category=Category.MEDS, preferred_time="08:00")

    plan = scheduler.generate_plan([meds_task], today="2026-07-06")

    assert "Medication" in plan.explanation


def test_retrieve_includes_species_note_alongside_category_guidance():
    """retrieve should merge the JSON category source with the Markdown species-notes source."""
    retriever = CareGuidanceRetriever()
    owner = make_owner()
    dog = Pet("Rex", species="dog")
    owner.add_pet(dog)
    walk_task = make_task(name="Morning Walk", category=Category.WALK)

    guidance = retriever.retrieve([walk_task], owner, top_k=3)

    assert any("early walk" in g for g in guidance)
    assert any("Dogs are highly exercise-driven" in g for g in guidance)


def test_retrieve_species_note_score_scales_with_pet_count():
    """A species with more pets should outrank a species with fewer, all else equal."""
    retriever = CareGuidanceRetriever()
    owner = make_owner()
    owner.add_pet(Pet("Rex", species="dog"))
    owner.add_pet(Pet("Fido", species="dog"))
    owner.add_pet(Pet("Luna", species="cat"))

    guidance = retriever.retrieve([], owner, top_k=1)

    assert "Dogs are highly exercise-driven" in guidance[0]


def test_retrieve_with_no_tasks_still_returns_species_note():
    """With no tasks scheduled, retrieve should still surface a matching species note."""
    retriever = CareGuidanceRetriever()
    owner = make_owner()
    owner.add_pet(Pet("Rex", species="dog"))

    guidance = retriever.retrieve([], owner, top_k=5)

    assert len(guidance) == 1
    assert "Dogs are highly exercise-driven" in guidance[0]
