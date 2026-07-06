# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

3 core tasks:
1. Add/configure a pet (and owner) profile
2. Add and manage care tasks
3. Generate and view today's plan

- Briefly describe your initial UML design.

Owner
Attributes: name, pets (list of Pet)
Methods: add_pet(pet)

Pet
Attributes: name, species, breed, tasks (list of Task)
Methods: add_task(task), remove_task(task)

Task
Attributes: name, category (walk/feeding/meds/etc.), duration (minutes), priority (high/med/low), preferred_time (optional)
Methods: __repr__() for clean display

Scheduler
Attributes: available_minutes, maybe start_time
Methods: generate_plan(tasks) → returns a Plan, plus helpers like sort_by_priority(), filter_by_time()

Plan
Attributes: scheduled_tasks (list), skipped_tasks (list), explanation
Methods: display()


- What classes did you include, and what responsibilities did you assign to each?

Owner — represents the human user and hold the link to their pet. It stores owner info, maintain the collection of pets.

Pet — the anchor that care tasks attach to. It stores the pet's identity (name, species, breed) and manage its own list of tasks (add/remove).

Task — describes a single care activity and its schedulin relevant data.

Scheduler — takes a set of tasks plus constraints (available time, priorities) and decide what gets scheduled, in what order, and what gets dropped. 

Plan — holds the output of the Scheduler: the ordered list of scheduled tasks, any skipped tasks, and the reasoning.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
1. Plan has no link back to Owner or Pet
- Owner.all_tasks() added (pawpal_system.py:79)

New method that returns list[tuple[Pet, Task]] — every task across all pets, paired with its pet so context isn't lost
- Plan.__init__ signature changed (pawpal_system.py:86)

Was: __init__(self)
Now: __init__(self, owner: "Owner", pet: Optional["Pet"] = None)
Stores both on self, so a plan always knows whose it is and which pet it covers (or None for a multi-pet plan)
2. Scheduler reads available_minutes from... itself, not Owner
Scheduler.__init__ signature changed (pawpal_system.py:102)
Was: __init__(self, available_minutes: int, ...)
Now: __init__(self, owner: "Owner", ...) — stores the owner and derives available_minutes from it rather than duplicating the value
3. No multi-pet aggregation path
Scheduler.generate_plan signature changed (pawpal_system.py:106)
Added optional pet parameter so the generated plan can be tagged to a specific pet when relevant
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

When two tasks overlap in time, the scheduler just drops the lower-priority one instead of trying to move it to a new time slot. In handle_conflicts, if a lower-priority task's preferred time overlaps with a higher-priority task that already took that slot, it gets removed from the plan and logged in skipped_tasks.
A fancier approach would try to bump the conflicting task to the next open slot. But that gets messy fast — moving one task could bump into another task, which bumps another, and so on. That's a lot of extra complexity for something as simple as a daily pet care schedule.
Dropping conflicts makes more sense here because pet care is time-sensitive. A 7 AM walk isn't really a "7 AM walk" anymore if it happens at 11 AM. Instead of silently moving tasks to random open times (which might not even make sense for the pet), it's better to flag the conflict with detect_conflicts and let the owner decide what to do.

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
