from pawpal_system import Event, Owner, Pet, Task, TimeSlot, Calendar
from datetime import date


def build_owner() -> Owner:
    owner = Owner("Alice")
    owner.add_pet(Pet("Buddy", "Dog", 5))
    owner.add_pet(Pet("Whiskers", "Cat", 3))
    return owner


def assign_tasks(owner: Owner) -> None:
    buddy, whiskers = owner.pets

    for task in [
        Task("Morning Walk", 30, "high",   "daily"),
        Task("Feeding",      15, "medium", "daily"),
    ]:
        buddy.tracker.add_task(task)

    whiskers.tracker.add_task(
        Task("Evening Playtime", 30, "low", "daily")
    )


def build_calendar() -> Calendar:
    calendar = Calendar()
    calendar.add_event(Event("Vet Appointment",  date(2026, 6, 15), TimeSlot("10:00", "11:00")))
    calendar.add_event(Event("Grooming Session", date(2026, 6, 20), TimeSlot("14:00", "15:00")))
    return calendar


def print_schedule(owner: Owner, calendar: Calendar) -> None:
    today = date.today()

    print(f"\nToday's Schedule ({today}) — {owner.name}'s Pets")
    print("-" * 45)
    for pet in owner.pets:
        tasks = pet.tracker.tasks
        if not tasks:
            print(f"  {pet.name} ({pet.species}): no tasks scheduled")
            continue
        for task in tasks:
            print(f"  [{task.priority.upper()}] {pet.name}: {task.name}  ({task.duration} min)")

    upcoming = [e for e in calendar.events if e.day >= today]
    if upcoming:
        print(f"\nUpcoming Calendar Events")
        print("-" * 45)
        for event in sorted(upcoming, key=lambda e: e.day):
            print(f"  {event.day}  {event.title}  {event.slot.start}–{event.slot.end}")


def main() -> None:
    owner    = build_owner()
    assign_tasks(owner)
    calendar = build_calendar()
    print_schedule(owner, calendar)


if __name__ == "__main__":
    main()
