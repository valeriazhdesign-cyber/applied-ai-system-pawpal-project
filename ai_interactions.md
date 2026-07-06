# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

Add a third algorithmic capability to PawPal+ beyond the existing `sort_by_priority` and `detect_conflicts` features, and document the work in this file. The instruction was: *"Add a third algorithmic capability (like 'next available slot', weighted prioritization, etc.) that goes beyond the basic requirements."*

**What did the agent do?**

The agent (Claude Code, Sonnet 4.6) made the following changes autonomously:

1. **Read** `pawpal_system.py`, `app.py`, and `ai_interactions.md` to understand the existing system before writing any code.

2. **Modified `pawpal_system.py`** — two additions:
   - `Task.weighted_score(today)`: a new method that computes a composite urgency float from four factors:
     - base priority rank × 10 (HIGH=30, MEDIUM=20, LOW=10)
     - category urgency (meds=5, feeding=4, walk=3, grooming=2, enrichment=1)
     - overdue-recurring bonus (+8 when a recurring task's window has elapsed)
     - efficiency nudge (0–1 favouring shorter tasks so more tasks fit per session)
   - `Scheduler.sort_by_weighted_priority(tasks, today)`: sorts by descending `weighted_score`, used as a drop-in alternative to `sort_by_priority`.
   - Updated `Scheduler.generate_plan(...)` signature with a `use_weighted_sort: bool = False` parameter that switches between the two sort strategies.

3. **Modified `app.py`** — two UI additions:
   - A `st.radio` "Sort mode" toggle ("Priority" vs "Smart Priority (Weighted)") in the task-preview section; when weighted mode is active, an **Urgency Score** column is appended to the table.
   - A `st.checkbox` "Use Smart Priority (Weighted) for schedule" above the Generate button that passes `use_weighted_sort` through to `generate_plan`.

Files modified: `pawpal_system.py`, `app.py`

**What did you have to verify or fix manually?**

One small correction was needed mid-task: the agent's first attempt added a module-level `_CATEGORY_URGENCY` dict that was flagged as unused by the IDE linter (it was defined but never read at module scope because the dict was going to be used only inside the method). The agent immediately reverted that approach and inlined the urgency mapping directly inside `Task.weighted_score`, eliminating the lint warning without any manual intervention beyond the IDE hint.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
