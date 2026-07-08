# Challenge 03 — Beans and Wiring

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Add a notifier.** Create a `Notifier` interface with a single method
   `void notify(String message)`. Provide two implementations:
   `ConsoleNotifier` (prints to stdout) and `NoOpNotifier` (does nothing).
   Make `ConsoleNotifier` the default by marking it `@Primary`. Inject the
   `Notifier` into `TaskService` and call it from `create(...)`.

2. **Multiple constructors.** Add a second constructor to `TaskService` that
   takes only `TaskRepository`. Use `@Autowired` on the *primary* one to
   tell Spring which to use. Confirm the app still starts and seeds the
   data.

3. **`@PostConstruct` and `@PreDestroy`.** Give `InMemoryTaskRepository` a
   `@PostConstruct` that prints `"repo ready"` and a `@PreDestroy` that
   prints `"repo closing"`. Restart the app and confirm both lines appear.

4. **Profile-scoped bean.** Add a `@Profile("dev")` `CommandLineRunner` that
   prints `"dev profile active"` when the `dev` profile is on. Activate it
   with `--spring.profiles.active=dev` and confirm; then run without the
   flag and confirm it's silent.

5. **Bean collision.** Create a second `@Service` `EagerTaskService` with
   the same `create(...)` shape as `TaskService`. Restart — what happens?
   Resolve it by giving one a `@Primary` or by using `@Qualifier("eager")`
   on the injection point.

6. **Stretch:** Make a `Map<String, Notifier>` bean that holds both
   `ConsoleNotifier` and `NoOpNotifier`, keyed by bean name. Inject it into
   a `NotificationRouter` that dispatches based on a header or query
   parameter. (This is the "Strategy" pattern, Spring-style.)

## Success criteria

- [ ] `Notifier` interface and two implementations exist; `ConsoleNotifier` is
  `@Primary`.
- [ ] `TaskService` is wired with the primary `Notifier` and calls it on
  create.
- [ ] Lifecycle hooks print on startup and shutdown.
- [ ] A `@Profile("dev")` bean only runs with the profile active.
- [ ] You can resolve a `NoUniqueBeanDefinitionException`.
- [ ] Stretch: a `Map<String, Notifier>` strategy router works.
