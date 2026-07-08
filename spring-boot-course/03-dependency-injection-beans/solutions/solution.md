# Challenge 03 — Reference Solution

### 1. Notifier interface + two implementations
```java
public interface Notifier { void notify(String message); }

@Component
@Primary
public class ConsoleNotifier implements Notifier {
    public void notify(String m) { System.out.println("[notify] " + m); }
}

@Component
public class NoOpNotifier implements Notifier {
    public void notify(String m) { }
}
```

Inject into `TaskService` and call from `create(...)`:
```java
public Task create(String title, String description) {
    if (title == null || title.isBlank()) throw new IllegalArgumentException("title is required");
    Task saved = repo.save(new Task(null, title.trim(), description, false, Instant.now(clock)));
    notifier.notify("created task " + saved.id());
    return saved;
}
```

### 2. Two constructors
```java
@Service
public class TaskService {
    private final TaskRepository repo;
    private final Clock clock;
    private final Notifier notifier;

    @Autowired
    public TaskService(TaskRepository repo, Clock clock, Notifier notifier) {
        this.repo = repo; this.clock = clock; this.notifier = notifier;
    }

    // for tests
    public TaskService(TaskRepository repo) {
        this(repo, Clock.systemUTC(), new NoOpNotifier());
    }
}
```

### 3. Lifecycle hooks
```java
@PostConstruct void init() { System.out.println("repo ready"); }
@PreDestroy  void close() { System.out.println("repo closing"); }
```
Restart: `repo ready` appears during startup, `repo closing` on shutdown.

### 4. Profile-scoped runner
```java
@Component
@Profile("dev")
public class DevRunner implements CommandLineRunner {
    public void run(String... args) { System.out.println("dev profile active"); }
}
```
```bash
mvn -q spring-boot:run -- --spring.profiles.active=dev
# → "dev profile active"
mvn -q spring-boot:run     # no flag → no output from DevRunner
```

### 5. Bean collision
With two `TaskService`-shaped beans:
```
NoUniqueBeanDefinitionException: expected single matching bean but found 2
```
Fix with `@Primary` on the real one, or `@Qualifier("eager")` on the
constructor parameter:
```java
public TaskService(@Qualifier("eagerTaskService") TaskRepository repo, ...) { ... }
```

### 6. Strategy router (stretch)
```java
@Component
public class NotificationRouter {
    private final Map<String, Notifier> byName;
    public NotificationRouter(List<Notifier> notifiers) {
        this.byName = notifiers.stream().collect(Collectors.toMap(
            n -> n.getClass().getSimpleName(), n -> n));
    }
    public void route(String target, String message) {
        Notifier n = byName.getOrDefault(target, byName.get("ConsoleNotifier"));
        n.notify(message);
    }
}
```
> This is the same trick Spring's `HttpMessageConverters` and
> `HandlerMethodArgumentResolver` collections use internally — collect
> every bean of a type into a `List` or `Map` and route on name.
