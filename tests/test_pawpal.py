import pytest
from datetime import date, timedelta, time as dtime
from pawpal_system import Task, TimeSlot, Event, Calendar, Tracker, Pet, Owner, Schedule, Scheduler

# ---------------------------------------------------------------------------
# Pure helpers mirrored from app.py (no Streamlit dependency)
# These duplicate only the filtering/sorting/conflict logic so we can test it
# independently of the Streamlit runtime.
# ---------------------------------------------------------------------------

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _tasks_due_on(pets_data: list, day: date, owner_name=None) -> list:
    """Return [(pet_name, species, task_dict), ...] sorted by priority."""
    due = []
    for p in pets_data:
        for t in p.get("tasks", []):
            if t["frequency"] == "daily":
                due.append((p["name"], p["species"], t))
            elif t["frequency"] == "weekly":
                tpw = t.get("times_per_week", 1)
                scheduled_days = {0}  # default: Monday only (no st.session_state needed)
                if day.weekday() in scheduled_days:
                    due.append((p["name"], p["species"], t))
            elif t["frequency"] == "monthly" and day.day == 1:
                due.append((p["name"], p["species"], t))
    due.sort(key=lambda x: PRIORITY_ORDER.get(x[2]["priority"], 3))
    return due


def _detect_conflicts(slots: list) -> list:
    """Return every (a, b) pair whose time windows overlap."""
    conflicts = []
    for i in range(len(slots)):
        for j in range(i + 1, len(slots)):
            a, b = slots[i], slots[j]
            if a["_start_raw"] < b["_end_raw"] and b["_start_raw"] < a["_end_raw"]:
                conflicts.append((a, b))
    return conflicts


def _conflict_severity(overlap_min: int) -> tuple:
    if overlap_min > 15:
        return "Major", "🔴", "#dc3545"
    elif overlap_min > 5:
        return "Moderate", "🟠", "#fd7e14"
    return "Minor", "🟡", "#ffc107"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def task_daily():
    return Task("Feeding", 15, "medium", "daily")

@pytest.fixture
def task_weekly():
    return Task("Bath", 30, "low", "weekly")

@pytest.fixture
def task_monthly():
    return Task("Vet Check", 60, "high", "monthly")

@pytest.fixture
def pet():
    return Pet("Buddy", "dog", 3)

@pytest.fixture
def owner():
    return Owner("Alice")

@pytest.fixture
def owner_with_pet(owner, pet):
    owner.add_pet(pet)
    return owner

@pytest.fixture
def tracker_with_tasks(task_daily, task_weekly, task_monthly):
    t = Tracker()
    t.add_task(task_daily)
    t.add_task(task_weekly)
    t.add_task(task_monthly)
    return t


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

class TestTask:
    def test_get_info_returns_all_fields(self, task_daily):
        info = task_daily.get_info()
        assert info["name"] == "Feeding"
        assert info["duration_minutes"] == 15
        assert info["priority"] == "medium"
        assert info["frequency"] == "daily"

    def test_repr(self, task_daily):
        assert "Feeding" in repr(task_daily)
        assert "daily" in repr(task_daily)


# ---------------------------------------------------------------------------
# TimeSlot
# ---------------------------------------------------------------------------

class TestTimeSlot:
    def test_repr(self):
        slot = TimeSlot("09:00", "10:00")
        assert "09:00" in repr(slot)
        assert "10:00" in repr(slot)


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------

class TestEvent:
    def test_repr(self):
        event = Event("Grooming", date(2026, 6, 1), TimeSlot("14:00", "15:00"))
        assert "Grooming" in repr(event)


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

class TestCalendar:
    def test_add_event_and_retrieve(self):
        cal = Calendar()
        event = Event("Vet", date(2026, 6, 15), TimeSlot("10:00", "11:00"))
        cal.add_event(event)
        assert event in cal.events

    def test_is_available_no_events(self):
        cal = Calendar()
        assert cal.is_available(date(2026, 6, 15)) is True

    def test_is_available_blocked_by_event(self):
        cal = Calendar()
        day = date(2026, 6, 15)
        cal.add_event(Event("Vet", day, TimeSlot("10:00", "11:00")))
        assert cal.is_available(day) is False

    def test_is_available_blocked_by_holiday(self):
        cal = Calendar()
        holiday = date(2026, 12, 25)
        cal.holidays.append(holiday)
        assert cal.is_available(holiday) is False

    def test_get_unavailable_times_returns_slots(self):
        cal = Calendar()
        slot = TimeSlot("10:00", "11:00")
        cal.add_event(Event("Vet", date(2026, 6, 15), slot))
        unavailable = cal.get_unavailable_times()
        assert slot in unavailable


# ---------------------------------------------------------------------------
# Tracker
# ---------------------------------------------------------------------------

class TestTracker:
    def test_add_task(self, task_daily):
        t = Tracker()
        t.add_task(task_daily)
        assert task_daily in t.tasks

    def test_add_task_no_duplicates(self, task_daily):
        t = Tracker()
        t.add_task(task_daily)
        t.add_task(task_daily)
        assert t.tasks.count(task_daily) == 1

    def test_remove_task(self, task_daily):
        t = Tracker()
        t.add_task(task_daily)
        t.remove_task(task_daily)
        assert task_daily not in t.tasks

    def test_edit_task(self, task_daily):
        t = Tracker()
        t.add_task(task_daily)
        updated = Task("Feeding", 20, "high", "daily")  # same name, different values
        t.edit_task(updated)
        assert t.tasks[0].duration == 20
        assert t.tasks[0].priority == "high"

    def test_edit_task_not_found_raises(self):
        t = Tracker()
        with pytest.raises(ValueError):
            t.edit_task(Task("Nonexistent", 10, "low", "daily"))

    def test_get_tasks_for_day_daily(self, task_daily):
        t = Tracker()
        t.add_task(task_daily)
        tasks = t.get_tasks_for_day(date.today())
        assert task_daily in tasks

    def test_get_tasks_for_day_weekly_on_monday(self, task_weekly):
        t = Tracker()
        t.add_task(task_weekly)
        monday = date(2026, 3, 30)  # a known Monday
        assert monday.weekday() == 0
        assert task_weekly in t.get_tasks_for_day(monday)

    def test_get_tasks_for_day_weekly_not_on_monday(self, task_weekly):
        t = Tracker()
        t.add_task(task_weekly)
        tuesday = date(2026, 3, 31)
        assert task_weekly not in t.get_tasks_for_day(tuesday)

    def test_get_tasks_for_day_monthly_on_first(self, task_monthly):
        t = Tracker()
        t.add_task(task_monthly)
        first = date(2026, 4, 1)
        assert task_monthly in t.get_tasks_for_day(first)

    def test_get_tasks_for_day_monthly_not_on_first(self, task_monthly):
        t = Tracker()
        t.add_task(task_monthly)
        second = date(2026, 4, 2)
        assert task_monthly not in t.get_tasks_for_day(second)

    def test_mark_task_completed(self, task_daily):
        t = Tracker()
        t.add_task(task_daily)
        today = date.today()
        t.mark_task_completed(task_daily, today)
        assert t.completion_log[(task_daily, today)] is True

    def test_get_upcoming_tasks_excludes_completed(self, task_daily):
        t = Tracker()
        t.add_task(task_daily)
        today = date.today()
        # daily task appears 7 times before any completion
        assert len(t.get_upcoming_tasks(today)) == 7
        # after marking today complete it should drop to 6
        t.mark_task_completed(task_daily, today)
        assert len(t.get_upcoming_tasks(today)) == 6

    def test_get_upcoming_tasks_includes_incomplete(self, task_daily):
        t = Tracker()
        t.add_task(task_daily)
        upcoming = t.get_upcoming_tasks(date.today())
        assert task_daily in upcoming

    def test_send_reminder_prints(self, task_daily, capsys):
        t = Tracker()
        owner = Owner("Alice")
        t.send_reminder(task_daily, date.today(), [owner])
        output = capsys.readouterr().out
        assert "Alice" in output
        assert "Feeding" in output


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

class TestPet:
    def test_get_info(self, pet):
        info = pet.get_info()
        assert info["name"] == "Buddy"
        assert info["species"] == "dog"
        assert info["age"] == 3

    def test_get_care_requirements_empty_initially(self, pet):
        assert pet.get_care_requirements() == []

    def test_get_care_requirements_after_adding_task(self, pet, task_daily):
        pet.tracker.add_task(task_daily)
        assert task_daily in pet.get_care_requirements()

    def test_get_preferences_dog(self, pet):
        prefs = pet.get_preferences()
        assert prefs["preferred_schedule"] == "morning"

    def test_get_preferences_other_species(self):
        fish = Pet("Nemo", "fish", 1)
        prefs = fish.get_preferences()
        assert prefs["preferred_schedule"] == "any"

    def test_owners_list_empty_initially(self, pet):
        assert pet.owners == []

    def test_repr(self, pet):
        assert "Buddy" in repr(pet)
        assert "dog" in repr(pet)


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class TestOwner:
    def test_get_info(self, owner_with_pet):
        info = owner_with_pet.get_info()
        assert info["name"] == "Alice"
        assert "Buddy" in info["pets"]

    def test_add_pet_links_both_sides(self, owner, pet):
        owner.add_pet(pet)
        assert pet in owner.pets
        assert owner in pet.owners

    def test_add_pet_no_duplicates(self, owner, pet):
        owner.add_pet(pet)
        owner.add_pet(pet)
        assert owner.pets.count(pet) == 1
        assert pet.owners.count(owner) == 1

    def test_remove_pet_unlinks_both_sides(self, owner, pet):
        owner.add_pet(pet)
        owner.remove_pet(pet)
        assert pet not in owner.pets
        assert owner not in pet.owners

    def test_shared_pet_two_owners(self, pet):
        alice = Owner("Alice")
        bob = Owner("Bob")
        alice.add_pet(pet)
        bob.add_pet(pet)
        assert alice in pet.owners
        assert bob in pet.owners
        assert pet in alice.pets
        assert pet in bob.pets

    def test_get_available_time(self, owner):
        slot = TimeSlot("08:00", "09:00")
        owner.available_time.append(slot)
        assert slot in owner.get_available_time()

    def test_get_preferences(self, owner):
        owner.preferences["walk_time"] = "morning"
        assert owner.get_preferences()["walk_time"] == "morning"

    def test_get_calendar(self, owner):
        assert owner.get_calendar() is owner.calendar

    def test_repr(self, owner):
        assert "Alice" in repr(owner)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class TestScheduler:
    def test_schedule_tasks_returns_schedule(self, owner, pet, task_daily):
        owner.add_pet(pet)
        pet.tracker.add_task(task_daily)
        scheduler = Scheduler()
        schedule = scheduler.schedule_tasks(owner, owner.pets)
        assert isinstance(schedule, Schedule)

    def test_schedule_contains_daily_tasks(self, owner, pet, task_daily):
        owner.add_pet(pet)
        pet.tracker.add_task(task_daily)
        scheduler = Scheduler()
        schedule = scheduler.schedule_tasks(owner, owner.pets)
        all_tasks = [task for entries in schedule.plan.values() for _, task in entries]
        assert task_daily in all_tasks

    def test_schedule_skips_unavailable_days(self, owner, pet, task_daily):
        owner.add_pet(pet)
        pet.tracker.add_task(task_daily)
        # block all 7 upcoming days
        for i in range(7):
            day = date.today() + timedelta(days=i)
            owner.calendar.add_event(Event("Busy", day, TimeSlot("00:00", "23:59")))
        scheduler = Scheduler()
        schedule = scheduler.schedule_tasks(owner, owner.pets)
        assert schedule.plan == {}

    def test_schedule_sorts_by_priority(self, owner, pet):
        owner.add_pet(pet)
        pet.tracker.add_task(Task("Low task",  10, "low",    "daily"))
        pet.tracker.add_task(Task("High task", 10, "high",   "daily"))
        pet.tracker.add_task(Task("Med task",  10, "medium", "daily"))
        scheduler = Scheduler()
        schedule = scheduler.schedule_tasks(owner, owner.pets)
        first_day = min(schedule.plan)
        task_names = [task.name for _, task in schedule.plan[first_day]]
        assert task_names.index("High task") < task_names.index("Med task")
        assert task_names.index("Med task") < task_names.index("Low task")

    def test_explain_schedule_empty(self, owner):
        scheduler = Scheduler()
        schedule = Schedule(owner, [])
        result = scheduler.explain_schedule(schedule)
        assert "No tasks" in result

    def test_explain_schedule_contains_owner_name(self, owner, pet, task_daily):
        owner.add_pet(pet)
        pet.tracker.add_task(task_daily)
        scheduler = Scheduler()
        schedule = scheduler.schedule_tasks(owner, owner.pets)
        explanation = scheduler.explain_schedule(schedule)
        assert "Alice" in explanation

    def test_explain_schedule_contains_task_and_pet(self, owner, pet, task_daily):
        owner.add_pet(pet)
        pet.tracker.add_task(task_daily)
        scheduler = Scheduler()
        schedule = scheduler.schedule_tasks(owner, owner.pets)
        explanation = scheduler.explain_schedule(schedule)
        assert "Buddy" in explanation
        assert "Feeding" in explanation

    def test_schedule_all_same_priority_all_included(self, owner, pet):
        owner.add_pet(pet)
        pet.tracker.add_task(Task("Task A", 10, "medium", "daily"))
        pet.tracker.add_task(Task("Task B", 10, "medium", "daily"))
        pet.tracker.add_task(Task("Task C", 10, "medium", "daily"))
        schedule = Scheduler().schedule_tasks(owner, owner.pets)
        all_tasks = [task for entries in schedule.plan.values() for _, task in entries]
        task_names = {t.name for t in all_tasks}
        assert {"Task A", "Task B", "Task C"} == task_names

    def test_schedule_unknown_priority_sorts_after_known(self, owner, pet):
        owner.add_pet(pet)
        pet.tracker.add_task(Task("Unknown", 10, "urgent", "daily"))  # not a valid priority
        pet.tracker.add_task(Task("Known", 10, "high", "daily"))
        schedule = Scheduler().schedule_tasks(owner, owner.pets)
        first_day = min(schedule.plan)
        task_names = [task.name for _, task in schedule.plan[first_day]]
        assert task_names.index("Known") < task_names.index("Unknown")


# ---------------------------------------------------------------------------
# Tracker — active_from edge cases
# ---------------------------------------------------------------------------

class TestTrackerActiveFrom:
    def test_task_hidden_before_active_from(self):
        t = Tracker()
        task = Task("Bath", 30, "low", "daily")
        task.active_from = date(2026, 6, 1)
        t.add_task(task)
        assert task not in t.get_tasks_for_day(date(2026, 5, 31))

    def test_task_visible_on_active_from_date(self):
        t = Tracker()
        task = Task("Bath", 30, "low", "daily")
        task.active_from = date(2026, 6, 1)
        t.add_task(task)
        assert task in t.get_tasks_for_day(date(2026, 6, 1))

    def test_task_visible_after_active_from(self):
        t = Tracker()
        task = Task("Bath", 30, "low", "daily")
        task.active_from = date(2026, 5, 1)
        t.add_task(task)
        assert task in t.get_tasks_for_day(date(2026, 6, 1))

    def test_weekly_task_hidden_before_active_from(self):
        t = Tracker()
        task = Task("Bath", 30, "low", "weekly")
        task.active_from = date(2026, 4, 6)  # a Monday
        t.add_task(task)
        prev_monday = date(2026, 3, 30)
        assert task not in t.get_tasks_for_day(prev_monday)

    def test_weekly_task_visible_on_active_from_monday(self):
        t = Tracker()
        task = Task("Bath", 30, "low", "weekly")
        task.active_from = date(2026, 3, 30)  # a Monday
        t.add_task(task)
        assert task in t.get_tasks_for_day(date(2026, 3, 30))


# ---------------------------------------------------------------------------
# _tasks_due_on — filtering and sorting edge cases
# ---------------------------------------------------------------------------

def _pet(name, tasks):
    """Helper: build a minimal pet dict for _tasks_due_on."""
    return {"name": name, "species": "dog", "tasks": tasks}


def _task(name, frequency, priority, duration=15):
    """Helper: build a minimal task dict for _tasks_due_on."""
    return {"name": name, "frequency": frequency, "priority": priority,
            "duration": duration, "times_per_week": 1, "times_per_day": 1}


MONDAY = date(2026, 3, 30)
TUESDAY = date(2026, 3, 31)
FIRST_OF_MONTH = date(2026, 4, 1)
SECOND_OF_MONTH = date(2026, 4, 2)


class TestTasksDueOnFiltering:
    def test_empty_pets_returns_empty(self):
        assert _tasks_due_on([], MONDAY) == []

    def test_pet_with_no_tasks_returns_empty(self):
        assert _tasks_due_on([_pet("Buddy", [])], MONDAY) == []

    def test_daily_task_appears_every_day(self):
        pet = _pet("Buddy", [_task("Feed", "daily", "medium")])
        for offset in range(7):
            day = MONDAY + timedelta(days=offset)
            result = _tasks_due_on([pet], day)
            assert len(result) == 1

    def test_weekly_task_appears_on_monday_only(self):
        pet = _pet("Buddy", [_task("Bath", "weekly", "low")])
        assert len(_tasks_due_on([pet], MONDAY)) == 1
        assert len(_tasks_due_on([pet], TUESDAY)) == 0

    def test_monthly_task_appears_on_first_only(self):
        pet = _pet("Buddy", [_task("Vet", "monthly", "high")])
        assert len(_tasks_due_on([pet], FIRST_OF_MONTH)) == 1
        assert len(_tasks_due_on([pet], SECOND_OF_MONTH)) == 0

    def test_daily_and_weekly_both_appear_on_monday(self):
        pet = _pet("Buddy", [
            _task("Feed", "daily", "medium"),
            _task("Bath", "weekly", "low"),
        ])
        result = _tasks_due_on([pet], MONDAY)
        names = [t["name"] for _, _, t in result]
        assert "Feed" in names
        assert "Bath" in names

    def test_multiple_pets_all_included(self):
        pets = [
            _pet("Buddy", [_task("Feed", "daily", "medium")]),
            _pet("Whiskers", [_task("Play", "daily", "low")]),
        ]
        result = _tasks_due_on(pets, MONDAY)
        pet_names = [pn for pn, _, _ in result]
        assert "Buddy" in pet_names
        assert "Whiskers" in pet_names


class TestTasksDueOnSorting:
    def test_high_before_medium_before_low(self):
        pet = _pet("Buddy", [
            _task("LowTask", "daily", "low"),
            _task("HighTask", "daily", "high"),
            _task("MedTask", "daily", "medium"),
        ])
        result = _tasks_due_on([pet], MONDAY)
        names = [t["name"] for _, _, t in result]
        assert names.index("HighTask") < names.index("MedTask")
        assert names.index("MedTask") < names.index("LowTask")

    def test_unknown_priority_sorts_after_all_known(self):
        pet = _pet("Buddy", [
            _task("UnknownTask", "daily", "urgent"),
            _task("LowTask", "daily", "low"),
            _task("HighTask", "daily", "high"),
        ])
        result = _tasks_due_on([pet], MONDAY)
        names = [t["name"] for _, _, t in result]
        assert names.index("HighTask") < names.index("UnknownTask")
        assert names.index("LowTask") < names.index("UnknownTask")

    def test_priority_order_constants(self):
        assert PRIORITY_ORDER["high"] < PRIORITY_ORDER["medium"]
        assert PRIORITY_ORDER["medium"] < PRIORITY_ORDER["low"]


# ---------------------------------------------------------------------------
# _detect_conflicts — overlap edge cases
# ---------------------------------------------------------------------------

def _slot(start_str, end_str, name=None):
    """Helper: build a slot dict with raw time fields for conflict detection."""
    h, m = start_str.split(":")
    start = dtime(int(h), int(m))
    h, m = end_str.split(":")
    end = dtime(int(h), int(m))
    return {
        "_start_raw": start,
        "_end_raw": end,
        "_task_raw": name or f"{start_str}-{end_str}",
        "_priority_raw": "medium",
    }


class TestDetectConflicts:
    def test_empty_list_no_conflicts(self):
        assert _detect_conflicts([]) == []

    def test_single_slot_no_conflicts(self):
        assert _detect_conflicts([_slot("09:00", "10:00")]) == []

    def test_sequential_slots_no_conflict(self):
        # end of a == start of b → no overlap
        a = _slot("09:00", "10:00")
        b = _slot("10:00", "11:00")
        assert _detect_conflicts([a, b]) == []

    def test_gap_between_slots_no_conflict(self):
        a = _slot("09:00", "10:00")
        b = _slot("10:30", "11:30")
        assert _detect_conflicts([a, b]) == []

    def test_partial_overlap_detected(self):
        a = _slot("09:00", "10:30")
        b = _slot("10:00", "11:00")
        assert len(_detect_conflicts([a, b])) == 1

    def test_identical_slots_conflict(self):
        a = _slot("09:00", "10:00", "A")
        b = _slot("09:00", "10:00", "B")
        assert len(_detect_conflicts([a, b])) == 1

    def test_complete_containment_is_conflict(self):
        outer = _slot("09:00", "11:00")
        inner = _slot("09:30", "10:30")
        assert len(_detect_conflicts([outer, inner])) == 1

    def test_three_slots_two_pairs_overlap(self):
        # a-b overlap, b-c overlap, a-c do not
        a = _slot("09:00", "10:30", "A")
        b = _slot("10:00", "11:30", "B")
        c = _slot("11:00", "12:00", "C")
        assert len(_detect_conflicts([a, b, c])) == 2

    def test_three_non_overlapping_no_conflicts(self):
        a = _slot("08:00", "09:00")
        b = _slot("09:00", "10:00")
        c = _slot("10:00", "11:00")
        assert _detect_conflicts([a, b, c]) == []


# ---------------------------------------------------------------------------
# _conflict_severity — boundary edge cases
# ---------------------------------------------------------------------------

class TestConflictSeverity:
    def test_major_above_15(self):
        label, _, _ = _conflict_severity(16)
        assert label == "Major"

    def test_major_large_overlap(self):
        label, _, _ = _conflict_severity(60)
        assert label == "Major"

    def test_moderate_exactly_15(self):
        # 15 is NOT > 15, so it falls into Moderate
        label, _, _ = _conflict_severity(15)
        assert label == "Moderate"

    def test_moderate_exactly_6(self):
        label, _, _ = _conflict_severity(6)
        assert label == "Moderate"

    def test_minor_exactly_5(self):
        # 5 is NOT > 5, so Minor
        label, _, _ = _conflict_severity(5)
        assert label == "Minor"

    def test_minor_small_overlap(self):
        label, _, _ = _conflict_severity(1)
        assert label == "Minor"

    def test_returns_label_emoji_color(self):
        label, emoji, color = _conflict_severity(20)
        assert isinstance(label, str) and label
        assert isinstance(emoji, str) and emoji
        assert color.startswith("#")

    def test_severity_increases_with_overlap(self):
        minor_label, _, _ = _conflict_severity(3)
        moderate_label, _, _ = _conflict_severity(10)
        major_label, _, _ = _conflict_severity(20)
        assert minor_label == "Minor"
        assert moderate_label == "Moderate"
        assert major_label == "Major"


# ---------------------------------------------------------------------------
# Sorting Correctness — tasks returned in chronological (day) order
# ---------------------------------------------------------------------------

class TestChronologicalOrdering:
    def test_schedule_plan_days_in_ascending_order(self, owner, pet, task_daily):
        """Days in the schedule plan must be in ascending date order."""
        owner.add_pet(pet)
        pet.tracker.add_task(task_daily)
        schedule = Scheduler().schedule_tasks(owner, owner.pets)
        days = list(schedule.plan.keys())
        assert days == sorted(days)

    def test_schedule_plan_only_contains_future_or_today(self, owner, pet, task_daily):
        """No scheduled day should be before today."""
        owner.add_pet(pet)
        pet.tracker.add_task(task_daily)
        schedule = Scheduler().schedule_tasks(owner, owner.pets)
        today = date.today()
        for day in schedule.plan:
            assert day >= today

    def test_schedule_plan_within_7_day_window(self, owner, pet, task_daily):
        """All scheduled days must fall within the 7-day look-ahead window."""
        owner.add_pet(pet)
        pet.tracker.add_task(task_daily)
        schedule = Scheduler().schedule_tasks(owner, owner.pets)
        today = date.today()
        for day in schedule.plan:
            assert day <= today + timedelta(days=6)

    def test_explain_schedule_days_printed_in_order(self, owner, pet, task_daily):
        """explain_schedule must list dates in ascending order."""
        from datetime import datetime as dt
        owner.add_pet(pet)
        pet.tracker.add_task(task_daily)
        schedule = Scheduler().schedule_tasks(owner, owner.pets)
        explanation = Scheduler().explain_schedule(schedule)
        # Lines look like "  Wednesday, March 29:" — parse the "Month DD" part
        day_dates = []
        for ln in explanation.splitlines():
            ln = ln.strip()
            if ln and ln[0].isalpha() and "," in ln and ln.endswith(":"):
                try:
                    date_part = ln.split(",", 1)[1].strip().rstrip(":")
                    day_dates.append(dt.strptime(date_part, "%B %d"))
                except ValueError:
                    pass
        assert day_dates == sorted(day_dates)

    def test_upcoming_tasks_ordered_day_by_day(self, task_daily):
        """get_upcoming_tasks iterates today → today+6; daily task appears once per day."""
        t = Tracker()
        t.add_task(task_daily)
        today = date.today()
        upcoming = t.get_upcoming_tasks(today)
        # One daily task × 7 days = 7 entries, each from a successive day
        assert len(upcoming) == 7


# ---------------------------------------------------------------------------
# Recurrence Logic — completing a task reschedules the next occurrence
# ---------------------------------------------------------------------------

class TestRecurrenceLogic:
    def test_completing_daily_task_sets_active_from_tomorrow(self, task_daily):
        """Marking a daily task done replaces it with a copy active from tomorrow."""
        t = Tracker()
        t.add_task(task_daily)
        today = date.today()
        t.mark_task_completed(task_daily, today)
        tomorrow = today + timedelta(days=1)
        new_tasks = [task for task in t.tasks if task.name == task_daily.name]
        assert len(new_tasks) == 1
        assert new_tasks[0].active_from == tomorrow

    def test_completed_daily_task_absent_on_completion_day(self, task_daily):
        """After completion, the task must not appear again on the same day."""
        t = Tracker()
        t.add_task(task_daily)
        today = date.today()
        t.mark_task_completed(task_daily, today)
        assert not any(task.name == task_daily.name for task in t.get_tasks_for_day(today))

    def test_completed_daily_task_reappears_tomorrow(self, task_daily):
        """The rescheduled daily task must appear the following day."""
        t = Tracker()
        t.add_task(task_daily)
        today = date.today()
        t.mark_task_completed(task_daily, today)
        tomorrow = today + timedelta(days=1)
        assert any(task.name == task_daily.name for task in t.get_tasks_for_day(tomorrow))

    def test_completing_weekly_task_reschedules_next_week(self, task_weekly):
        """Marking a weekly task done sets active_from to 7 days later."""
        t = Tracker()
        t.add_task(task_weekly)
        today = date.today()
        t.mark_task_completed(task_weekly, today)
        next_week = today + timedelta(days=7)
        new_tasks = [task for task in t.tasks if task.name == task_weekly.name]
        assert len(new_tasks) == 1
        assert new_tasks[0].active_from == next_week

    def test_completing_monthly_task_leaves_it_in_tracker(self, task_monthly):
        """Monthly tasks have no auto-reschedule, so the original stays in the tracker."""
        t = Tracker()
        t.add_task(task_monthly)
        today = date.today()
        t.mark_task_completed(task_monthly, today)
        assert task_monthly in t.tasks

    def test_rescheduled_task_preserves_priority_and_duration(self, task_daily):
        """The rescheduled copy must carry over priority and duration unchanged."""
        t = Tracker()
        t.add_task(task_daily)
        today = date.today()
        t.mark_task_completed(task_daily, today)
        new_task = next(task for task in t.tasks if task.name == task_daily.name)
        assert new_task.priority == task_daily.priority
        assert new_task.duration == task_daily.duration
        assert new_task.frequency == task_daily.frequency


# ---------------------------------------------------------------------------
# Conflict Detection — Scheduler flags duplicate / overlapping times
# ---------------------------------------------------------------------------

class TestSchedulerConflictDetection:
    def test_duplicate_start_time_is_a_conflict(self):
        """Two tasks starting at the exact same time must be flagged."""
        a = _slot("09:00", "10:00", "Feeding")
        b = _slot("09:00", "10:00", "Bath")
        conflicts = _detect_conflicts([a, b])
        assert len(conflicts) == 1

    def test_conflict_pair_names_both_tasks(self):
        """The returned pair must reference both conflicting task names."""
        a = _slot("09:00", "10:30", "Feeding")
        b = _slot("10:00", "11:00", "Bath")
        conflicts = _detect_conflicts([a, b])
        assert len(conflicts) == 1
        slot_a, slot_b = conflicts[0]
        names = {slot_a["_task_raw"], slot_b["_task_raw"]}
        assert names == {"Feeding", "Bath"}

    def test_no_conflict_when_tasks_are_sequential(self):
        """Tasks placed back-to-back (no gap) must not be flagged."""
        a = _slot("09:00", "10:00", "Feeding")
        b = _slot("10:00", "11:00", "Bath")
        assert _detect_conflicts([a, b]) == []

    def test_multiple_overlapping_pairs_all_flagged(self):
        """Every overlapping pair in a busy day must each appear in the conflict list."""
        a = _slot("08:00", "09:30", "Task A")
        b = _slot("09:00", "10:30", "Task B")
        c = _slot("10:00", "11:30", "Task C")
        # a-b overlap, b-c overlap; a-c do not
        conflicts = _detect_conflicts([a, b, c])
        assert len(conflicts) == 2

    def test_only_overlapping_pair_flagged_not_sequential(self):
        """A mix of overlapping and sequential tasks: only the overlapping pair flagged."""
        a = _slot("08:00", "09:00", "Task A")   # sequential with b
        b = _slot("09:00", "10:30", "Task B")   # overlaps c
        c = _slot("10:00", "11:00", "Task C")
        conflicts = _detect_conflicts([a, b, c])
        flagged_names = [{s["_task_raw"] for s in pair} for pair in conflicts]
        assert {"Task B", "Task C"} in flagged_names
        assert {"Task A", "Task B"} not in flagged_names


# ---------------------------------------------------------------------------
# Scheduling engine helpers (mirrored from app.py — no Streamlit dependency)
# Used by TestTimesPerDay and TestBusyTimeExclusion below.
# ---------------------------------------------------------------------------

from datetime import datetime as _dt


def _add_minutes(t: dtime, minutes: int) -> dtime:
    d = _dt.combine(date.today(), t) + timedelta(minutes=minutes)
    return d.time().replace(second=0, microsecond=0)


def _block_minutes_local(s: dtime, e: dtime) -> int:
    return max(1, int((_dt.combine(date.today(), e) - _dt.combine(date.today(), s)).total_seconds() // 60))


def _distribute_occurrences(n: int, bm_list: list) -> list:
    """Proportionally distribute n occurrences across blocks sized bm_list."""
    total = sum(bm_list)
    raw = [n * bm / total for bm in bm_list]
    counts = [int(r) for r in raw]
    remainder = n - sum(counts)
    fractions = sorted(enumerate(raw), key=lambda x: -(x[1] - int(x[1])))
    for j in range(remainder):
        counts[fractions[j][0]] += 1
    return counts


def _build_slots(entries: list, free_blocks: list) -> list:
    """
    Minimal replica of app._build_slots that places tasks inside free_blocks.
    Single-occurrence tasks are stacked sequentially; multi-occurrence tasks
    are spread evenly across blocks, one per sub-interval.
    Returns a list of slot dicts with raw metadata keys.
    """
    if not free_blocks:
        return []

    slots = []
    single = [(p, sp, t) for p, sp, t in entries if t.get("times_per_day", 1) <= 1]
    multi  = [(p, sp, t) for p, sp, t in entries if t.get("times_per_day", 1) > 1]

    # Single-occurrence: stack from the start of the first free block
    blk_idx = 0
    cursor = free_blocks[0][0]
    for pet_name, _, t in single:
        task_end = _add_minutes(cursor, t["duration"])
        while blk_idx < len(free_blocks) - 1:
            _, blk_end = free_blocks[blk_idx]
            if _dt.combine(date.today(), task_end) > _dt.combine(date.today(), blk_end):
                blk_idx += 1
                cursor = free_blocks[blk_idx][0]
                task_end = _add_minutes(cursor, t["duration"])
            else:
                break
        slots.append({
            "_start_raw": cursor, "_end_raw": task_end,
            "_task_raw": t["name"], "_priority_raw": t["priority"],
            "_dur_raw": t["duration"], "_pet_raw": pet_name,
        })
        cursor = task_end

    # Multi-occurrence: center each occurrence within evenly-sized sub-intervals
    bm_list = [_block_minutes_local(s, e) for s, e in free_blocks]
    for pet_name, _, t in multi:
        n = t.get("times_per_day", 1)
        counts = _distribute_occurrences(n, bm_list)
        for bi, (blk_start, _) in enumerate(free_blocks):
            n_in_blk = counts[bi]
            if n_in_blk == 0:
                continue
            interval = bm_list[bi] / n_in_blk
            for i in range(n_in_blk):
                offset = int(i * interval + interval / 2)
                occ_start = _add_minutes(blk_start, offset)
                occ_end   = _add_minutes(occ_start, t["duration"])
                slots.append({
                    "_start_raw": occ_start, "_end_raw": occ_end,
                    "_task_raw": t["name"], "_priority_raw": t["priority"],
                    "_dur_raw": t["duration"], "_pet_raw": pet_name,
                })

    slots.sort(key=lambda x: _dt.combine(date.today(), x["_start_raw"]))
    return slots


def _entry(name, duration, times_per_day=1, priority="medium", pet="Buddy"):
    """Shorthand to build a scheduling entry tuple."""
    return (pet, "dog", {
        "name": name, "frequency": "daily", "priority": priority,
        "duration": duration, "times_per_day": times_per_day, "times_per_week": 1,
    })


_FULL_DAY = [(dtime(8, 0), dtime(20, 0))]   # 12-hour uninterrupted free window


# ---------------------------------------------------------------------------
# Times-per-day — multi-occurrence tasks spread across the day
# ---------------------------------------------------------------------------

class TestTimesPerDay:
    def test_correct_slot_count(self):
        """times_per_day=3 must produce exactly 3 scheduled slots."""
        slots = _build_slots([_entry("Feed", 30, times_per_day=3)], _FULL_DAY)
        assert len(slots) == 3

    def test_single_occurrence_produces_one_slot(self):
        """Default (times_per_day=1) must still yield exactly one slot."""
        slots = _build_slots([_entry("Feed", 30, times_per_day=1)], _FULL_DAY)
        assert len(slots) == 1

    def test_all_occurrences_have_distinct_start_times(self):
        """Each occurrence must start at a different time — none are simultaneous."""
        slots = _build_slots([_entry("Feed", 20, times_per_day=4)], _FULL_DAY)
        starts = [s["_start_raw"] for s in slots]
        assert len(set(starts)) == len(starts), "Some occurrences share the same start time"

    def test_occurrences_spread_across_the_day(self):
        """With 3 occurrences across 8:00–20:00, the first should be AM, last PM."""
        slots = _build_slots([_entry("Feed", 20, times_per_day=3)], _FULL_DAY)
        starts = sorted(s["_start_raw"] for s in slots)
        assert starts[0] < dtime(12, 0), "First occurrence not in the morning"
        assert starts[-1] >= dtime(12, 0), "Last occurrence not in the afternoon"

    def test_occurrences_returned_in_chronological_order(self):
        """_build_slots must return slots sorted by start time, not insertion order."""
        slots = _build_slots([_entry("Feed", 20, times_per_day=4)], _FULL_DAY)
        starts = [s["_start_raw"] for s in slots]
        assert starts == sorted(starts)

    def test_two_occurrences_split_across_two_free_blocks(self):
        """times_per_day=2 with two separate free blocks → one occurrence per block."""
        two_blocks = [(dtime(8, 0), dtime(9, 0)), (dtime(17, 0), dtime(18, 0))]
        slots = _build_slots([_entry("Feed", 20, times_per_day=2)], two_blocks)
        assert len(slots) == 2
        starts = [s["_start_raw"] for s in slots]
        in_morning   = any(dtime(8, 0) <= s < dtime(9, 0)  for s in starts)
        in_afternoon = any(dtime(17, 0) <= s < dtime(18, 0) for s in starts)
        assert in_morning,   "No occurrence placed in the morning block"
        assert in_afternoon, "No occurrence placed in the afternoon block"

    def test_task_name_preserved_across_all_occurrences(self):
        """Every slot must carry the correct task name regardless of occurrence number."""
        slots = _build_slots([_entry("Medicine", 10, times_per_day=3)], _FULL_DAY)
        assert all(s["_task_raw"] == "Medicine" for s in slots)


# ---------------------------------------------------------------------------
# Busy-time exclusion — tasks must stay within declared free blocks
# ---------------------------------------------------------------------------

class TestBusyTimeExclusion:
    # Owner free: 08:00–09:00 and 17:00–20:00; busy 09:00–17:00
    _SPLIT_BLOCKS = [(dtime(8, 0), dtime(9, 0)), (dtime(17, 0), dtime(20, 0))]

    def test_no_slots_when_no_free_blocks(self):
        """Empty free_blocks must produce zero scheduled slots."""
        assert _build_slots([_entry("Feed", 30)], []) == []

    def test_single_task_placed_inside_free_block(self):
        """Task start and end must both fall within the declared free window."""
        free = [(dtime(9, 0), dtime(11, 0))]
        slots = _build_slots([_entry("Feed", 30)], free)
        assert len(slots) == 1
        assert slots[0]["_start_raw"] >= dtime(9, 0)
        assert slots[0]["_end_raw"]   <= dtime(11, 0)

    def test_task_not_scheduled_during_busy_period(self):
        """With a 9:00–17:00 busy block, no task start should fall in that window."""
        slots = _build_slots([_entry("Feed", 30)], self._SPLIT_BLOCKS)
        for s in slots:
            assert not (dtime(9, 0) <= s["_start_raw"] < dtime(17, 0)), (
                f"Task scheduled during busy period at {s['_start_raw']}"
            )

    def test_multi_occurrence_task_avoids_busy_period(self):
        """times_per_day=2 must place both occurrences outside the busy window."""
        slots = _build_slots([_entry("Feed", 20, times_per_day=2)], self._SPLIT_BLOCKS)
        assert len(slots) == 2
        for s in slots:
            assert not (dtime(9, 0) <= s["_start_raw"] < dtime(17, 0)), (
                f"Occurrence scheduled during busy period at {s['_start_raw']}"
            )

    def test_multiple_pets_all_respect_free_blocks(self):
        """Tasks from different pets must all start within the same free window."""
        free = [(dtime(9, 0), dtime(11, 0))]
        entries = [
            _entry("Feed", 15, pet="Buddy"),
            _entry("Play", 15, pet="Whiskers"),
        ]
        slots = _build_slots(entries, free)
        assert len(slots) == 2
        for s in slots:
            assert s["_start_raw"] >= dtime(9, 0)
            assert s["_end_raw"]   <= dtime(11, 0)

    def test_task_overflowing_block_advances_to_next_block(self):
        """A task too long for the first block must spill into the next free block."""
        tight_then_wide = [(dtime(8, 0), dtime(8, 10)), (dtime(17, 0), dtime(20, 0))]
        # 30-min task can't fit in the 10-min first block → should land in second block
        slots = _build_slots([_entry("LongTask", 30)], tight_then_wide)
        assert len(slots) == 1
        assert slots[0]["_start_raw"] >= dtime(17, 0), (
            "Long task should have moved to the second free block"
        )


# ---------------------------------------------------------------------------
# Scheduler.complete_task — covers lines 281-282 (the coverage gap)
# ---------------------------------------------------------------------------

class TestSchedulerCompleteTask:
    def test_complete_task_returns_tomorrow_for_daily(self, pet, task_daily):
        """complete_task must return today+1 for a daily task."""
        pet.tracker.add_task(task_daily)
        today = date.today()
        next_due = Scheduler().complete_task(task_daily, pet, today)
        assert next_due == today + timedelta(days=1)

    def test_complete_task_returns_next_week_for_weekly(self, pet, task_weekly):
        """complete_task must return today+7 for a weekly task."""
        pet.tracker.add_task(task_weekly)
        today = date.today()
        next_due = Scheduler().complete_task(task_weekly, pet, today)
        assert next_due == today + timedelta(days=7)

    def test_complete_task_returns_none_for_monthly(self, pet, task_monthly):
        """complete_task must return None for a monthly task (no auto-reschedule)."""
        pet.tracker.add_task(task_monthly)
        result = Scheduler().complete_task(task_monthly, pet, date.today())
        assert result is None

    def test_complete_task_marks_completion_in_tracker(self, pet, task_daily):
        """Calling complete_task must record the completion in the pet's tracker log."""
        pet.tracker.add_task(task_daily)
        today = date.today()
        Scheduler().complete_task(task_daily, pet, today)
        assert pet.tracker.completion_log.get((task_daily, today)) is True


# ---------------------------------------------------------------------------
# Tracker.get_upcoming_tasks — weekly and monthly frequencies
# ---------------------------------------------------------------------------

class TestUpcomingTasksFrequencies:
    def test_weekly_task_appears_at_most_once_in_7_days(self, task_weekly):
        """A weekly task has at most one Monday in any 7-day window."""
        t = Tracker()
        t.add_task(task_weekly)
        upcoming = t.get_upcoming_tasks(date.today())
        assert len(upcoming) <= 1

    def test_weekly_task_appears_once_when_window_starts_on_monday(self, task_weekly):
        """Starting the window on a Monday guarantees exactly one weekly occurrence."""
        monday = date(2026, 3, 30)
        t = Tracker()
        t.add_task(task_weekly)
        upcoming = t.get_upcoming_tasks(monday)
        assert len(upcoming) == 1

    def test_monthly_task_appears_once_when_window_includes_first(self, task_monthly):
        """Starting on the 1st means the monthly task appears exactly once."""
        first = date(2026, 4, 1)
        t = Tracker()
        t.add_task(task_monthly)
        upcoming = t.get_upcoming_tasks(first)
        assert len(upcoming) == 1

    def test_monthly_task_absent_when_window_misses_first(self, task_monthly):
        """A window that doesn't include the 1st must return zero monthly tasks."""
        second = date(2026, 4, 2)
        t = Tracker()
        t.add_task(task_monthly)
        upcoming = t.get_upcoming_tasks(second)
        assert len(upcoming) == 0


# ---------------------------------------------------------------------------
# Tracker.remove_task — removing a task not in the list raises ValueError
# ---------------------------------------------------------------------------

class TestTrackerRemoveNotFound:
    def test_remove_absent_task_raises(self):
        """Removing a task that was never added must raise ValueError."""
        t = Tracker()
        phantom = Task("Ghost", 10, "low", "daily")
        with pytest.raises(ValueError):
            t.remove_task(phantom)


# ---------------------------------------------------------------------------
# Pet.get_preferences — cat also prefers "morning"
# ---------------------------------------------------------------------------

class TestPetPreferencesCat:
    def test_cat_prefers_morning(self):
        """Cats are in the same group as dogs → preferred_schedule == 'morning'."""
        cat = Pet("Whiskers", "cat", 4)
        assert cat.get_preferences()["preferred_schedule"] == "morning"

    def test_rabbit_prefers_any(self):
        """Species outside dog/cat fall back to 'any'."""
        rabbit = Pet("Thumper", "rabbit", 2)
        assert rabbit.get_preferences()["preferred_schedule"] == "any"


# ---------------------------------------------------------------------------
# Calendar — multiple events on the same day
# ---------------------------------------------------------------------------

class TestCalendarMultipleEvents:
    def test_two_events_same_day_both_returned_as_unavailable(self):
        """get_unavailable_times must list slots from every event, not just the first."""
        cal = Calendar()
        day = date(2026, 6, 10)
        slot_a = TimeSlot("09:00", "10:00")
        slot_b = TimeSlot("14:00", "15:00")
        cal.add_event(Event("Vet", day, slot_a))
        cal.add_event(Event("Grooming", day, slot_b))
        unavailable = cal.get_unavailable_times()
        assert slot_a in unavailable
        assert slot_b in unavailable

    def test_is_available_false_with_multiple_events(self):
        """is_available must return False as long as any event falls on that day."""
        cal = Calendar()
        day = date(2026, 6, 10)
        cal.add_event(Event("Vet", day, TimeSlot("09:00", "10:00")))
        cal.add_event(Event("Grooming", day, TimeSlot("14:00", "15:00")))
        assert cal.is_available(day) is False

    def test_multiple_holidays_all_blocked(self):
        """Every date in the holidays list must be treated as unavailable."""
        cal = Calendar()
        cal.holidays.extend([date(2026, 12, 25), date(2026, 1, 1)])
        assert cal.is_available(date(2026, 12, 25)) is False
        assert cal.is_available(date(2026, 1, 1)) is False


# ---------------------------------------------------------------------------
# Completion-log identity — rescheduled task is a NEW object
# ---------------------------------------------------------------------------

class TestCompletionLogIdentity:
    def test_new_task_object_not_in_old_completion_log(self, task_daily):
        """After rescheduling, the new Task object must NOT appear in the old log."""
        t = Tracker()
        t.add_task(task_daily)
        today = date.today()
        t.mark_task_completed(task_daily, today)
        new_task = next(task for task in t.tasks if task.name == task_daily.name)
        # The new object is different from the original
        assert new_task is not task_daily
        # The new object has no completion entry for today
        assert t.completion_log.get((new_task, today)) is None

    def test_original_task_completion_still_logged(self, task_daily):
        """The original task's completion entry must remain intact after rescheduling."""
        t = Tracker()
        t.add_task(task_daily)
        today = date.today()
        t.mark_task_completed(task_daily, today)
        assert t.completion_log[(task_daily, today)] is True


# ---------------------------------------------------------------------------
# Shared pet — independent schedules per owner
# ---------------------------------------------------------------------------

class TestSharedPetScheduleIsolation:
    def test_two_owners_share_pet_get_independent_schedules(self, pet, task_daily):
        """Each owner's schedule_tasks call must return a separate Schedule object."""
        alice = Owner("Alice")
        bob = Owner("Bob")
        alice.add_pet(pet)
        bob.add_pet(pet)
        pet.tracker.add_task(task_daily)
        scheduler = Scheduler()
        sched_alice = scheduler.schedule_tasks(alice, alice.pets)
        sched_bob   = scheduler.schedule_tasks(bob,   bob.pets)
        assert sched_alice is not sched_bob
        assert sched_alice.owner is alice
        assert sched_bob.owner is bob

    def test_blocking_one_owners_calendar_does_not_affect_other(self, pet, task_daily):
        """Blocking Alice's calendar must not affect Bob's schedule for the same pet."""
        alice = Owner("Alice")
        bob = Owner("Bob")
        alice.add_pet(pet)
        bob.add_pet(pet)
        pet.tracker.add_task(task_daily)
        # Block all 7 days for Alice
        for i in range(7):
            day = date.today() + timedelta(days=i)
            alice.calendar.add_event(Event("Busy", day, TimeSlot("00:00", "23:59")))
        scheduler = Scheduler()
        assert scheduler.schedule_tasks(alice, alice.pets).plan == {}
        assert scheduler.schedule_tasks(bob, bob.pets).plan != {}


# ---------------------------------------------------------------------------
# _distribute_occurrences — edge cases
# ---------------------------------------------------------------------------

class TestDistributeOccurrences:
    def test_single_occurrence_lands_in_largest_block(self):
        """n=1 with unequal blocks → the sole occurrence goes to the biggest block."""
        counts = _distribute_occurrences(1, [60, 120, 30])
        assert sum(counts) == 1
        assert counts[1] == 1  # index 1 is the 120-min block

    def test_occurrences_equal_blocks_one_each(self):
        """When n equals the number of blocks each block gets exactly one."""
        counts = _distribute_occurrences(3, [60, 60, 60])
        assert counts == [1, 1, 1]

    def test_total_always_equals_n(self):
        """The sum of distributed counts must always equal n."""
        for n, blocks in [(5, [30, 60, 90]), (7, [10, 20]), (1, [100])]:
            assert sum(_distribute_occurrences(n, blocks)) == n

    def test_larger_block_gets_more_occurrences(self):
        """A block twice as large should receive at least as many occurrences."""
        counts = _distribute_occurrences(4, [30, 90])   # 1:3 ratio
        assert counts[1] >= counts[0]
