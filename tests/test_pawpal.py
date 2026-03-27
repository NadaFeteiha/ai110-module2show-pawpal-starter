import pytest
from datetime import date, timedelta
from pawpal_system import Task, TimeSlot, Event, Calendar, Tracker, Pet, Owner, Schedule, Scheduler


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
