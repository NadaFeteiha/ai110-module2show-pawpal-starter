from datetime import date, timedelta
from typing import List, Dict, Tuple


class TimeSlot:
    def __init__(self, start: str, end: str):
        self.start = start  # e.g. "09:00"
        self.end = end      # e.g. "10:00"

    def __repr__(self) -> str:
        """Return a string representation of the time slot."""
        return f"{self.start} - {self.end}"


class Event:
    def __init__(self, title: str, day: date, slot: TimeSlot):
        self.title = title
        self.day = day
        self.slot = slot

    def __repr__(self) -> str:
        """Return a string representation of the event."""
        return f"{self.title} on {self.day} ({self.slot})"


class Task:
    def __init__(self, name: str, duration: int, priority: str, frequency: str):
        self.name = name
        self.duration = duration   # in minutes
        self.priority = priority   # "high", "medium", "low"
        self.frequency = frequency # "daily", "weekly", "monthly"

    def get_info(self) -> Dict:
        """Return a dictionary of task details."""        
        return {
            "name": self.name,
            "duration_minutes": self.duration,
            "priority": self.priority,
            "frequency": self.frequency,
        }

    def __repr__(self) -> str:
        """Return a concise string representation of the task."""
        return f"Task({self.name}, {self.frequency})"


class Schedule:
    def __init__(self, owner: "Owner", pets: List["Pet"]):
        """ 
        Initialize a schedule for the given owner and their pets.
        The schedule will be built based on the tasks associated with each pet.
        """
        self.owner = owner
        self.pets = pets
        self.plan: Dict[date, List[Tuple["Pet", Task]]] = {}

    def add_entry(self, day: date, pet: "Pet", task: Task):
        """Add a (pet, task) entry to the plan for the given day."""
        if day not in self.plan:
            self.plan[day] = []
        self.plan[day].append((pet, task))


class Tracker:
    def __init__(self):
        """ Initialize the tracker with an empty list of tasks and an empty completion log.
        The completion log is a dictionary that maps (task, date) tuples to a boolean indicating whether the task was completed on that date.
        """
        self.tasks: List[Task] = []
        self.completion_log: Dict[Tuple[Task, date], bool] = {}

    def add_task(self, task: Task):
        """Add a task to the tracker, ignoring duplicates."""
        if task not in self.tasks:
            self.tasks.append(task)

    def edit_task(self, updated_task: Task):
        """Replace the task that shares the same name with the updated version."""
        for i, task in enumerate(self.tasks):
            if task.name == updated_task.name:
                self.tasks[i] = updated_task
                return
        raise ValueError(f"Task '{updated_task.name}' not found in tracker.")

    def remove_task(self, task: Task):
        """Remove a task from the tracker."""
        self.tasks.remove(task)

    def get_tasks_for_day(self, day: date) -> List[Task]:
        """Return tasks that are due on the given day based on their frequency."""
        due = []
        for task in self.tasks:
            if task.frequency == "daily":
                due.append(task)
            elif task.frequency == "weekly" and day.weekday() == 0:  # every Monday
                due.append(task)
            elif task.frequency == "monthly" and day.day == 1:       # first of month
                due.append(task)
        return due

    def mark_task_completed(self, task: Task, day: date):
        """Record a task as completed for the given day."""
        self.completion_log[(task, day)] = True

    def send_reminder(self, task: Task, day: date, owners: List["Owner"]):
        """Print a reminder to each owner about an upcoming or missed task."""
        for owner in owners:
            print(f"Reminder → {owner.name}: '{task.name}' is due on {day}")

    def get_upcoming_tasks(self, day: date) -> List[Task]:
        """Return tasks due in the next 7 days that are not yet completed."""
        upcoming = []
        for i in range(7):
            future_day = day + timedelta(days=i)
            for task in self.get_tasks_for_day(future_day):
                if not self.completion_log.get((task, future_day), False):
                    upcoming.append(task)
        return upcoming


class Pet:
    def __init__(self, name: str, species: str, age: int):
        self.name = name
        self.species = species
        self.age = age
        self.tracker: Tracker = Tracker()
        self.owners: List["Owner"] = []  # many-to-many: a pet can have multiple owners

    def get_info(self) -> Dict:
        """Return a dictionary of the pet's details including its owners."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "owners": [owner.name for owner in self.owners],
        }

    def get_care_requirements(self) -> List[Task]:
        """Return all tasks registered in this pet's tracker."""
        return self.tracker.tasks

    def get_preferences(self) -> Dict:
        """Return scheduling preferences inferred from the pet's species."""
        return {
            "species": self.species,
            "preferred_schedule": "morning" if self.species.lower() in ["dog", "cat"] else "any",
        }

    def __repr__(self) -> str:
        """Return a concise string representation of the pet."""
        return f"Pet({self.name}, {self.species})"


class Calendar:
    def __init__(self):
        self.events: List[Event] = []
        self.holidays: List[date] = []

    def add_event(self, event: Event):
        """Add an event to the calendar."""
        self.events.append(event)

    def get_unavailable_times(self) -> List[TimeSlot]:
        """Return all time slots occupied by scheduled events."""
        return [event.slot for event in self.events]

    def is_available(self, day: date) -> bool:
        """Return True if the day has no events and is not a holiday."""
        if day in self.holidays:
            return False
        return not any(event.day == day for event in self.events)


class Owner:
    def __init__(self, name: str):
        self.name = name
        self.available_time: List[TimeSlot] = []
        self.preferences: Dict = {}
        self.calendar: Calendar = Calendar()
        self.pets: List[Pet] = []

    def get_info(self) -> Dict:
        """Return a dictionary of the owner's details including pets and preferences."""
        return {
            "name": self.name,
            "pets": [pet.name for pet in self.pets],
            "preferences": self.preferences,
            "available_slots": [str(slot) for slot in self.available_time],
        }

    def get_available_time(self) -> List[TimeSlot]:
        """Return the owner's list of available time slots."""
        return self.available_time

    def get_preferences(self) -> Dict:
        """Return the owner's scheduling preferences."""
        return self.preferences

    def get_calendar(self) -> Calendar:
        """Return the owner's calendar."""
        return self.calendar

    def add_pet(self, pet: Pet):
        """Link pet to this owner (both sides of the relationship)."""
        if pet not in self.pets:
            self.pets.append(pet)
        if self not in pet.owners:
            pet.owners.append(self)

    def remove_pet(self, pet: Pet):
        """Unlink pet from this owner (both sides of the relationship)."""
        if pet in self.pets:
            self.pets.remove(pet)
        if self in pet.owners:
            pet.owners.remove(self)

    def __repr__(self) -> str:
        """Return a concise string representation of the owner."""
        return f"Owner({self.name})"


class Scheduler:
    _PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def schedule_tasks(self, owner: Owner, pets: List[Pet]) -> Schedule:
        """
        Build a 7-day schedule for all of the owner's pets.
        Skips days where the owner is unavailable.
        Tasks are sorted by priority within each day.
        """
        schedule = Schedule(owner, pets)
        today = date.today()

        for i in range(7):
            day = today + timedelta(days=i)
            if not owner.calendar.is_available(day):
                continue
            for pet in pets:
                tasks_for_day = pet.tracker.get_tasks_for_day(day)
                tasks_for_day.sort(key=lambda t: self._PRIORITY_ORDER.get(t.priority, 3))
                for task in tasks_for_day:
                    schedule.add_entry(day, pet, task)

        return schedule

    def explain_schedule(self, schedule: Schedule) -> str:
        """Return a human-readable summary of the schedule."""
        if not schedule.plan:
            return "No tasks scheduled for the coming week."

        lines = [f"Weekly schedule for {schedule.owner.name}:"]
        for day in sorted(schedule.plan):
            lines.append(f"\n  {day.strftime('%A, %B %d')}:")
            for pet, task in schedule.plan[day]:
                lines.append(
                    f"    - [{task.priority.upper()}] {pet.name}: "
                    f"{task.name} ({task.duration} min, {task.frequency})"
                )
        return "\n".join(lines)
