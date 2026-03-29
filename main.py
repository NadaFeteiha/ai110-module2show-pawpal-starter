from pawpal_system import Event, Owner, Pet, Task, TimeSlot, Calendar, Scheduler
from datetime import date, timedelta
from typing import List


# ---------------------------------------------------------------------------
# Sorting helpers
# ---------------------------------------------------------------------------

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def sort_tasks(tasks: List[Task], by: str) -> List[Task]:
    """
    Sort a list of tasks by the given criterion.
    by: "priority" | "duration_asc" | "duration_desc" | "name"
    """
    if by == "priority":
        return sorted(tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 3))
    elif by == "duration_asc":
        return sorted(tasks, key=lambda t: t.duration)
    elif by == "duration_desc":
        return sorted(tasks, key=lambda t: t.duration, reverse=True)
    elif by == "name":
        return sorted(tasks, key=lambda t: t.name.lower())
    return tasks


# ---------------------------------------------------------------------------
# Filtering helpers
# ---------------------------------------------------------------------------

def filter_by_pet(owner: Owner, pet_name: str) -> List[Task]:
    """Return all tasks belonging to the named pet."""
    for pet in owner.pets:
        if pet.name.lower() == pet_name.lower():
            return list(pet.tracker.tasks)
    return []


def filter_by_completion(
    tasks: List[Task],
    tracker,
    day: date,
    completed: bool,
) -> List[Task]:
    """
    Return tasks that are (or are not) marked complete for the given day.
    completed=True  → tasks logged in completion_log for that day
                      (these may already be removed from tracker.tasks and replaced)
    completed=False → tasks still in tracker.tasks with no completion entry for that day
    """
    if completed:
        # Completed tasks may have been removed from tracker.tasks, so read the log directly
        return [task for (task, d) in tracker.completion_log if d == day]
    else:
        return [t for t in tasks if not tracker.completion_log.get((t, day), False)]


# ---------------------------------------------------------------------------
# Build data
# ---------------------------------------------------------------------------

def build_owner() -> Owner:
    owner = Owner("Alice")
    owner.add_pet(Pet("Buddy",    "Dog", 5))
    owner.add_pet(Pet("Whiskers", "Cat", 3))
    owner.add_pet(Pet("Tweety",   "Bird", 1))
    return owner


def assign_tasks_out_of_order(owner: Owner) -> None:
    """Add tasks deliberately out of priority/duration order to exercise sorting."""
    buddy, whiskers, tweety = owner.pets

    # Buddy — added low → monthly → medium → high (reverse of natural priority order)
    for task in [
        Task("Evening Stroll",  45, "low",    "daily"),
        Task("Flea Treatment",  10, "medium", "monthly"),
        Task("Feeding",         15, "medium", "daily"),
        Task("Morning Walk",    30, "high",   "daily"),
        Task("Bath Time",       60, "low",    "weekly"),
    ]:
        buddy.tracker.add_task(task)

    # Whiskers — mixed durations
    for task in [
        Task("Litter Box Clean", 10, "high",   "daily"),
        Task("Evening Playtime", 30, "low",    "daily"),
        Task("Grooming",         20, "medium", "weekly"),
        Task("Vet Check",         5, "high",   "monthly"),
    ]:
        whiskers.tracker.add_task(task)

    # Tweety
    for task in [
        Task("Cage Clean",  15, "medium", "weekly"),
        Task("Feeding",      5, "high",   "daily"),
        Task("Socialise",   20, "low",    "daily"),
    ]:
        tweety.tracker.add_task(task)


def build_calendar() -> Calendar:
    cal = Calendar()
    cal.add_event(Event("Vet Appointment",  date(2026, 6, 15), TimeSlot("10:00", "11:00")))
    cal.add_event(Event("Grooming Session", date(2026, 6, 20), TimeSlot("14:00", "15:00")))
    return cal


# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------

def _header(title: str) -> None:
    print(f"\n{'=' * 55}")
    print(f"  {title}")
    print(f"{'=' * 55}")


def _print_tasks(tasks: List[Task], indent: int = 2) -> None:
    pad = " " * indent
    if not tasks:
        print(f"{pad}(no tasks)")
        return
    for t in tasks:
        print(f"{pad}[{t.priority.upper():<6}] {t.name:<22} {t.duration:>3} min  {t.frequency}")


def _print_day_tasks(pet: Pet, day: date) -> None:
    tasks = pet.tracker.get_tasks_for_day(day)
    if tasks:
        for t in tasks:
            print(f"    [{t.priority.upper():<6}] {t.name}")
    else:
        print(f"    (nothing due)")


# ---------------------------------------------------------------------------
# Demo sections
# ---------------------------------------------------------------------------

def demo_raw(owner: Owner) -> None:
    _header("RAW (insertion order — out of order)")
    for pet in owner.pets:
        print(f"\n  {pet.name} ({pet.species}):")
        _print_tasks(pet.tracker.tasks)


def demo_sort(owner: Owner) -> None:
    modes = [
        ("priority",      "Sort by Priority"),
        ("duration_asc",  "Sort by Duration ↑"),
        ("duration_desc", "Sort by Duration ↓"),
        ("name",          "Sort by Name"),
    ]
    all_tasks = [t for pet in owner.pets for t in pet.tracker.tasks]
    for mode, label in modes:
        _header(label)
        _print_tasks(sort_tasks(all_tasks, mode))


def demo_filter_by_pet(owner: Owner) -> None:
    _header("Filter by Pet — Buddy only")
    _print_tasks(filter_by_pet(owner, "Buddy"))

    _header("Filter by Pet — Whiskers only")
    _print_tasks(filter_by_pet(owner, "Whiskers"))


def demo_filter_by_completion(owner: Owner, today: date) -> None:
    buddy = owner.pets[0]

    # Mark the high-priority tasks as done for today
    done_tasks = [t for t in buddy.tracker.tasks if t.priority == "high"]
    for t in done_tasks:
        buddy.tracker.mark_task_completed(t, today)

    _header(f"Buddy — Done today ({today})")
    _print_tasks(filter_by_completion(buddy.tracker.tasks, buddy.tracker, today, completed=True))

    _header(f"Buddy — Not done today ({today})")
    _print_tasks(filter_by_completion(buddy.tracker.tasks, buddy.tracker, today, completed=False))


def demo_combined(owner: Owner, today: date) -> None:
    buddy = owner.pets[0]
    pending = filter_by_completion(buddy.tracker.tasks, buddy.tracker, today, completed=False)
    _header("Buddy — Pending tasks sorted by Duration ↑")
    _print_tasks(sort_tasks(pending, "duration_asc"))


# ---------------------------------------------------------------------------
# Auto-reschedule demo
# ---------------------------------------------------------------------------

def _print_tracker_list(tracker, label: str) -> None:
    print(f"\n  {label}")
    if not tracker.tasks:
        print("    (empty)")
        return
    for t in tracker.tasks:
        note = f"  [active from {t.active_from}]" if t.active_from else ""
        print(f"    {t.name:<22} {t.frequency:<8}{note}")


def demo_auto_reschedule(owner: Owner, today: date) -> None:
    scheduler = Scheduler()
    buddy = owner.pets[0]

    daily_task  = next(t for t in buddy.tracker.tasks if t.frequency == "daily")
    weekly_task = next(t for t in buddy.tracker.tasks if t.frequency == "weekly")
    monthly_task = next(t for t in buddy.tracker.tasks if t.frequency == "monthly")

    tomorrow    = today + timedelta(days=1)
    last_monday = today - timedelta(days=today.weekday())
    next_monday = last_monday + timedelta(days=7)

    # ── Daily task ───────────────────────────────────────────────────────────
    _header(f"DAILY TASK — '{daily_task.name}'")

    _print_tracker_list(buddy.tracker, "tracker.tasks BEFORE completion:")
    print(f"\n  Due today    ({today}):    {daily_task.name in [t.name for t in buddy.tracker.get_tasks_for_day(today)]}")
    print(f"  Due tomorrow ({tomorrow}): {daily_task.name in [t.name for t in buddy.tracker.get_tasks_for_day(tomorrow)]}")

    next_due = scheduler.complete_task(daily_task, buddy, today)
    print(f"\n  ✓ Marked complete on {today}  →  next occurrence: {next_due}")

    _print_tracker_list(buddy.tracker, "tracker.tasks AFTER completion (old instance replaced):")
    print(f"\n  Due today    ({today}):    {daily_task.name in [t.name for t in buddy.tracker.get_tasks_for_day(today)]}")
    print(f"  Due tomorrow ({tomorrow}): {daily_task.name in [t.name for t in buddy.tracker.get_tasks_for_day(tomorrow)]}")

    # ── Weekly task ──────────────────────────────────────────────────────────
    _header(f"WEEKLY TASK — '{weekly_task.name}'")

    _print_tracker_list(buddy.tracker, "tracker.tasks BEFORE completion:")
    print(f"\n  Due on {last_monday} (Monday):      {weekly_task.name in [t.name for t in buddy.tracker.get_tasks_for_day(last_monday)]}")
    print(f"  Due on {next_monday} (next Mon): {weekly_task.name in [t.name for t in buddy.tracker.get_tasks_for_day(next_monday)]}")

    next_due = scheduler.complete_task(weekly_task, buddy, last_monday)
    print(f"\n  ✓ Marked complete on {last_monday}  →  next occurrence: {next_due}")

    _print_tracker_list(buddy.tracker, "tracker.tasks AFTER completion (old instance replaced):")
    print(f"\n  Due on {last_monday} (Monday):      {weekly_task.name in [t.name for t in buddy.tracker.get_tasks_for_day(last_monday)]}")
    print(f"  Due on {next_monday} (next Mon): {weekly_task.name in [t.name for t in buddy.tracker.get_tasks_for_day(next_monday)]}")

    # ── Monthly task — no auto-reschedule ────────────────────────────────────
    _header(f"MONTHLY TASK — '{monthly_task.name}' (no replacement)")

    _print_tracker_list(buddy.tracker, "tracker.tasks BEFORE completion:")
    next_due = scheduler.complete_task(monthly_task, buddy, today)
    print(f"\n  ✓ Marked complete on {today}  →  next_due: {next_due}  (None — stays in list unchanged)")
    _print_tracker_list(buddy.tracker, "tracker.tasks AFTER completion (unchanged):")

    # ── 7-day view ───────────────────────────────────────────────────────────
    _header("7-DAY SCHEDULE — Buddy (after all completions above)")
    print()
    for i in range(7):
        day = today + timedelta(days=i)
        label = "today    " if i == 0 else ("tomorrow " if i == 1 else day.strftime("%A   "))
        print(f"  {label} {day}:")
        _print_day_tasks(buddy, day)


def demo_upcoming_calendar(owner: Owner, cal: Calendar) -> None:
    _header("Upcoming Calendar Events")
    today = date.today()
    upcoming = sorted([e for e in cal.events if e.day >= today], key=lambda e: e.day)
    if upcoming:
        for e in upcoming:
            print(f"  {e.day}  {e.title:<22} {e.slot.start}–{e.slot.end}")
    else:
        print("  (none)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    today    = date.today()
    owner    = build_owner()
    assign_tasks_out_of_order(owner)
    calendar = build_calendar()

    demo_raw(owner)
    demo_sort(owner)
    demo_filter_by_pet(owner)
    demo_filter_by_completion(owner, today)
    demo_combined(owner, today)
    demo_auto_reschedule(owner, today)
    demo_upcoming_calendar(owner, calendar)

    print("\n")


if __name__ == "__main__":
    main()
