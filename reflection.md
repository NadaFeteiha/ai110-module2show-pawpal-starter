# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

so I will need owner that will have account and could be able to have multiple pets, and each pet will have its own set of tasks, and the scheduler will need to consider the owner's available time and preferences when generating a daily plan.

Also should be abele that the pet could have multiple owner so they could share the care tasks and schedule.

there will be a Tracker class that will manage the tasks for each pet and each day because some tasks are daily and some are weekly or monthly, and the Scheduler class will need to consider the frequency of each task when generating the schedule.

the scheduler need to have access to the owner's calendar to avoid scheduling tasks during times when the owner is unavailable and also to consider the holidays or special events that might affect services such as grooming or vet visits.

the tracker will also need to keep track of the completion status daily and able to send reminders to the owner for upcoming tasks or missed tasks.

the initial UML design included the following classes:

class Pet:
    - Attributes: name, species, age
    - Methods: get_info(), get_care_requirements(), get_preferences()

class Tracker:
    - Attributes: tasks (list of Task objects)
    - Methods: add_task(), edit_task(), remove_task(),get_tasks_for_day(date),mark_task_completed(task, date),send_reminder(task, date),get_upcoming_tasks(date)

class owner:
    - Attributes: name, available_time,preferences, calendar, pets (list of Pet objects)
    - Methods: get_info(),get_available_time(), get_preferences(), get_calendar(), add_pet(pet), remove_pet(pet)

class Scheduler:
    - Attributes: None (or any necessary attributes for scheduling)
    - Methods: schedule_tasks(owner, pet, tasks),explain_schedule(schedule)

class Task:
    - Attributes: name, duration, priority, frequency
    - Methods: get_info(), get_duration(), get_priority(), get_frequency()


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, the design changed during implementation. One change I made was to add a new class called "Task" to represent individual care tasks for pets. Initially, I had planned to include the task information directly within the Tracker class, but I realized that it would be more organized and modular to have a separate Task class. This change allowed me to better manage the attributes and methods related to tasks, such as duration, priority, and frequency, and made it easier to extend the functionality of tasks in the future if needed.

Another change I made was to modify the Scheduler class to handle conflicts between tasks and the owner's availability because after implemented the scheduling logic, I realized that it was important to ensure that tasks were not scheduled during times when the owner was unavailable. This led me to add a new method in the Scheduler class to check for conflicts and adjust the schedule accordingly, which improved the overall functionality of the system.

Another thing I considered later is the task if daily or weekly etc should be considered how many times it should be scheduled in a day and so on. The frequency attribute in the Task class was added to handle scheduling and ensure that tasks are scheduled appropriately based on their frequency requirements.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

My scheduler considers several constraints, including:
- Time: The scheduler takes into account the duration of each task and the owner's available time to ensure that tasks are scheduled within the owner's schedule.
- Priority: Tasks are assigned a priority level, and the scheduler prioritizes higher-priority tasks when generating the schedule.
- Preferences: The scheduler considers the owner's preferences for certain tasks, such as preferred times for feeding or walking the pet, and tries to accommodate those preferences when scheduling tasks.

---

- How did you decide which constraints mattered most?

I decided that time and priority were the most important constraints for the scheduler because they directly impact the feasibility and effectiveness of the schedule. Time is a critical constraint because it determines when tasks can be scheduled and ensures that the owner can realistically complete the tasks within their available time. Priority is also crucial because it helps to ensure that the most important tasks are completed first, which is essential for the well-being of the pet. Preferences are also important, but they are secondary to time and priority because they can be adjusted or accommodated as needed, whereas time and priority are more rigid constraints that must be adhered to for the schedule to be effective.
---

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

One tradeoff my scheduler makes is between accommodating the owner's preferences and ensuring that high-priority tasks are scheduled. For example, if the owner prefers to walk their dog in the evening, but the scheduler determines that feeding the pet (a high-priority task) needs to be scheduled during that time, the scheduler may choose to schedule the feeding task during the preferred walking time and reschedule the walk for a different time. This tradeoff allows the scheduler to prioritize important tasks while still trying to accommodate the owner's preferences as much as possible.

---

- Why is that tradeoff reasonable for this scenario?

This tradeoff is reasonable for this scenario because it ensures that the most critical tasks for the pet's care are prioritized while still making an effort to respect the owner's preferences. The well-being of the pet is the primary concern, and ensuring that high-priority tasks are completed is essential for their health and happiness. At the same time, accommodating the owner's preferences can help to increase their satisfaction with the schedule and make it more likely that they will adhere to it. By striking a balance between these two factors, the scheduler can create a schedule that is both effective for the pet's care and acceptable to the owner.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

I used AI tools in all phases of the project, different way in each phase. 
for design brainstorming, I used AI agent to help generate the uml and also chating to cosider what else did I need to consider in the design and what are the responsibilities of each class and how they interact with each other, and that helped me to have a clear design and also to be able to change and refactor the design easily.

later for implementation, I used AI to help me write the code for the skeleton of the system, and that helped me to focus on the important parts of the implementation and also to save time by not having to write boilerplate code.

for testing and debugging, I used AI to help me generate test cases and also to help me identify and fix bugs in the code. The AI was able to analyze the code and suggest potential issues, which helped me to quickly identify and resolve problems.

Also after I found some issues I used it to refactor the test case and the other function that depend on this one to make sure that the code is clean and maintainable.

---

- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

the handeling of the frequency of the task was a bit tricky because I wanted to make sure that the scheduler can handle tasks that need to be scheduled multiple times a day or week, and the AI suggested implementation that did not consider the frequency of the tasks. 

Also the completion status ; in the first it was implemented as full task completed not one of the frequency completed, but I wanted to make sure that the owner can mark a task as partially completed if they have completed one of the frequency requirements but not all of them, and the AI suggested implementation did not consider that aspect.
---

- How did you evaluate or verify what the AI suggested?
I read the AI's suggestions also I ask if I don't get it. and if I accepted the suggestion I tested it to make sure that it works as expected. after multiple iterations I ask to evaluate and tell me the cases that not handel and if this code implemented effectively and how and why so I can understand the suggestion better and also to make sure that I am not missing any important aspect of the implementation.
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
I tested several behaviors of the scheduler, including:
- Scheduling tasks based on the owner's available time and preferences.
- Prioritizing tasks based on their priority level.
- Handling conflicts between tasks and the owner's schedule.
- Managing multiple pets and their respective tasks.
- Tracking the completion status of tasks and sending reminders for upcoming or missed tasks.

---

- Why were these tests important?
These tests were important because they helped to ensure that the scheduler was functioning correctly and effectively. By testing the scheduling logic, I was able to verify that tasks were being scheduled appropriately based on the owner's constraints and preferences. Testing the prioritization of tasks helped to confirm that high-priority tasks were being scheduled first, which is crucial for the well-being of the pet. Testing for conflicts between tasks and the owner's schedule ensured that the scheduler was generating realistic and feasible schedules. Additionally, testing the management of multiple pets and their tasks helped to confirm that the system could handle more complex scenarios. Finally, testing the tracking of task completion and reminders was important to ensure that the system could effectively support the owner in managing their pet's care.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
I liked that i was care to design a simple uml and write a word then I be able to convert it to reaal diagram and that help me to figure out the classes and their responsibilities and how they interact with each other, and that made it easier to change and refactor the design and later I was able to implement the skeleton of the system.

The most important and satisfying part focse on what matters and what is the important like classes and their responsibilities and relationships between them and ignoring the details that could be added later with simple implementations.

---

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
