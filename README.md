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

## Features

| Feature | Description |
|---|---|
| **Multi-pet support** | Add multiple pets under one owner; tasks are tracked per pet |
| **Priority scheduling** | Tasks sorted high → medium → low; low-priority tasks dropped first when time runs out |
| **Time-slot hints** | Each task declares a preferred slot (morning / afternoon / evening / anytime); scheduler places tasks into the right part of the day |
| **Recurring tasks** | Mark a task `daily` or `weekly`; the next occurrence is automatically queued with an updated due date |
| **Sort by time** | View any task list ordered chronologically by time slot |
| **Filter tasks** | Narrow the task list by pet name and/or completion status |
| **Conflict detection** | Schedule is scanned for overlapping tasks; warnings shown in the UI without crashing |
| **Explain plan** | Every scheduled task includes a human-readable reason explaining when and why it was placed |

## Demo

To run the app locally:

```bash
source .venv/bin/activate
streamlit run app.py
```

## Smarter Scheduling

The scheduler now includes three algorithmic improvements beyond basic priority ordering:

- **Sort by time** — `Scheduler.sort_by_time(tasks)` orders any task list chronologically by preferred time slot (morning → anytime → afternoon → evening) using a `lambda` key with `sorted()`.
- **Filter tasks** — `Scheduler.filter_tasks(pet_name, completed)` lets you narrow the full task pool by pet and/or completion status, making it easy to see only what is still pending for a specific animal.
- **Recurring tasks** — Tasks can be marked `frequency="daily"` or `frequency="weekly"`. Calling `pet.complete_task(task)` marks it done and automatically re-queues a fresh copy with a `due_date` of `today + 1 day` (or `+ 7 days`), so recurring care never falls off the list.
- **Conflict detection** — `Scheduler.detect_conflicts(schedule)` scans every pair of scheduled tasks and returns a warning string for any that overlap in time, without crashing the program.

## Testing PawPal+

Run the full test suite with:

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

The suite contains **21 tests** covering:

| Area | What is verified |
|---|---|
| Task completion | `mark_complete()` flips status; completed tasks are excluded from schedule |
| Recurrence | Daily tasks create a next-day copy; weekly tasks create a next-week copy; one-off tasks do not re-queue |
| Pet management | `add_task()` stamps `pet_name`; task count increases correctly |
| Edge cases | Pet with zero tasks produces empty schedule; one-off tasks don't re-queue |
| Sorting | `sort_by_time()` returns morning → anytime → afternoon → evening order |
| Filtering | `filter_tasks()` correctly narrows by pet name and completion status |
| Scheduling | Respects `available_minutes`; high priority before low priority |
| Conflict detection | Overlapping tasks flagged; exact same start time flagged; sequential tasks clear; generated schedule always conflict-free |

**Confidence level: ★★★★☆** — All happy paths and the main edge cases are covered. Edge cases not yet tested: tasks that span midnight, owners with zero pets, very large task pools near the time limit.

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
