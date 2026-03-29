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

## Smarter Scheduling

PawPal+ goes beyond a simple task list — it actively detects and helps resolve scheduling conflicts so your pet care plan is always realistic.

### Conflict Detection

Every day in the 7-day schedule is scanned for overlapping task windows. Two tasks conflict when their assigned time ranges overlap (i.e. one starts before the other ends). Conflicts are classified by severity based on how much time overlaps:

| Severity | Overlap | Indicator |
|----------|---------|-----------|
| Minor    | 1–5 min | 🟡 Yellow |
| Moderate | 6–15 min | 🟠 Orange |
| Major    | > 15 min | 🔴 Red |

### Conflict UI

When conflicts are found for a day, a **color-coded summary banner** appears immediately — no need to dig through the schedule to notice a problem. For each conflict, the detail panel shows:

- **Side-by-side task cards** with time range and priority for both tasks
- **Visual timeline bar** — blue and green blocks for each task, with the overlap highlighted in red, all scaled proportionally to the available time window
- **Priority-aware suggestion** — automatically identifies which task has the lower priority and recommends shortening it to eliminate the overlap
- **Auto-fix button** — one click applies the recommended fix instantly
- **Manual override inputs** — adjust either task's duration to any value if you prefer a custom resolution

The expander auto-opens for Major and Moderate conflicts so critical issues are never missed, and stays collapsed for Minor ones to keep the view clean.

### Time-Aware Scheduling

Tasks are distributed across the owner's free time blocks for each day:

- **Single-occurrence tasks** are stacked sequentially from the start of the first free block, automatically advancing to the next block if a task would overflow.
- **Multi-occurrence tasks** (e.g. feeding 3×/day) are spread evenly across all free blocks, with each occurrence centered within its sub-interval.
- **Busy windows** (e.g. work hours) are respected — tasks are only placed in the gaps before and after the busy period.

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
