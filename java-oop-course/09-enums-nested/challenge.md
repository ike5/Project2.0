# Challenge 09 — Enums, Nested & Inner Classes

Solution in [`solutions/`](./solutions/). Try first.

## Tasks

1. **A `Priority` enum with a comparator.** Build `enum Priority { LOW,
   MEDIUM, HIGH, URGENT }` and use it to implement
   `Comparator<Priority>` such that `URGENT > HIGH > MEDIUM > LOW`.
   Confirm `Priority.values()` is in declaration order.

2. **A `WorkflowStep` state machine.** Build a `WorkflowStep` enum with
   `DRAFT, IN_REVIEW, APPROVED, REJECTED, PUBLISHED` and constant-specific
   methods `submit()`, `approve()`, `reject()`, `publish()`. Each method
   returns the next valid step, or the current step for invalid
   transitions. Demonstrate the happy path
   `DRAFT → IN_REVIEW → APPROVED → PUBLISHED`.

3. **A static nested `Node` for a `DoublyLinkedList`.** Build a tiny
   `DoublyLinkedList<E>` with a static nested `Node<E>` (with `value`,
   `prev`, `next`) and a method `reverse()` that reverses the list in
   place. Iterate with an enhanced for.

4. **An `EnumMap<Day, Schedule>` week.** Build `enum Day { MON, ... SUN }`
   and a `record Schedule(String activity)`. Build a
   `Map<Day, Schedule>` using `EnumMap` and `Map.of` literals for
   week-day and weekend schedules. Print them in `Day.values()` order.

5. **Replace an anonymous class with a lambda.** Take any example from
   earlier modules (e.g. `list.sort(new Comparator<…>() { … })`) and
   rewrite it with a lambda. Note the line-count reduction.

## Success criteria

- [ ] `Priority` enum has a working `Comparator` via the enum's natural
      `ordinal`-based ordering.
- [ ] `WorkflowStep` enforces valid transitions; invalid ones are no-ops.
- [ ] `DoublyLinkedList.reverse` works in place.
- [ ] `EnumMap` iteration is in `Day.values()` order.
- [ ] The lambda replacement is one line shorter (or more) than the
      anonymous class.
