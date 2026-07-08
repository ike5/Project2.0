# Challenge 01 — Java in the Wild

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

Open the [`code/tasklib`](./code/tasklib/) project from the lab. Add a new
class `Stats.java` with a `main` method that, given a `TaskStore`, prints:

1. **Total tasks and open tasks.** Two numbers, one line. Use `stream().count()`.
2. **Titles grouped by first letter.** A `Map<Character, List<String>>` from a
   `Collectors.groupingBy(...)`. Print each letter and its titles.
3. **Longest title.** Use `max(Comparator)` on a stream; print just the title.
4. **Search with no results.** Call `findByTitleContains("zzz")` and use
   `Optional` to print "no matches" instead of throwing.
5. **Custom exception.** Define `TaskNotFoundException extends
   RuntimeException`. Add a `delete(long id)` method to `TaskStore` that
   throws it if the id doesn't exist. Call it with a bad id from `main` and
   catch the exception.
6. **Stretch:** Add a `@JsonField`-style annotation `@Since("1.1")` to *some*
   methods of a class, then write a small reflection helper that lists every
   annotated method with its version. (This is exactly what libraries like
   Jackson do to decide what's serializable.)

## Success criteria

- [ ] `Stats.main` prints total and open counts.
- [ ] Titles are grouped by first letter.
- [ ] The longest title is printed (or "no tasks" if empty).
- [ ] A search with no results prints "no matches" via `Optional`, not a
  `NullPointerException`.
- [ ] A custom exception is defined, thrown, and caught.
- [ ] Stretch: a reflection helper lists annotated methods.
