# Challenge 01 — Reference Solution

`src/main/java/com/example/tasklib/Stats.java`:

```java
package com.example.tasklib;
import java.util.*;
import java.util.stream.Collectors;

public class Stats {
    public static void main(String[] args) {
        TaskStore store = new TaskStore();
        store.create("Buy milk");
        store.create("Fix login bug");
        store.create("Write docs");
        store.create("Refactor auth");
        store.markDone(2);

        long total = store.findOpen().size() + store.findAllDone().size();
        long open  = store.findOpen().size();
        System.out.printf("total=%d open=%d%n", total, open);

        var byLetter = store.all().stream()
            .collect(Collectors.groupingBy(t -> Character.toUpperCase(t.title().charAt(0)),
                                            Collectors.mapping(Task::title, Collectors.toList())));
        byLetter.forEach((k, v) -> System.out.println(k + " -> " + v));

        store.all().stream()
            .max(Comparator.comparingInt(t -> t.title().length()))
            .map(Task::title)
            .ifPresentOrElse(t -> System.out.println("longest: " + t),
                             () -> System.out.println("no tasks"));

        store.findByTitleContains("zzz")
            .stream().findAny()
            .map(Task::title)
            .ifPresentOrElse(t -> System.out.println("found: " + t),
                             () -> System.out.println("no matches"));

        try {
            store.delete(9999);
        } catch (TaskNotFoundException e) {
            System.out.println("caught: " + e.getMessage());
        }
    }
}
```

Add to `TaskStore.java`:
```java
public List<Task> findAllDone() { return byId.values().stream().filter(Task::done).toList(); }
public List<Task> all()         { return List.copyOf(byId.values()); }
public void delete(long id) {
    if (!byId.containsKey(id)) throw new TaskNotFoundException("no task " + id);
    byId.remove(id);
}
```

`TaskNotFoundException`:
```java
package com.example.tasklib;
public class TaskNotFoundException extends RuntimeException {
    public TaskNotFoundException(String m) { super(m); }
}
```

### Stretch — annotated method listing

```java
@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD)
public @interface Since { String value(); }

class Sample {
    @Since("1.0") public void old() {}
    @Since("1.1") public void newer() {}
}

public static void listSince(Object o) {
    for (var m : o.getClass().getDeclaredMethods()) {
        Since s = m.getAnnotation(Since.class);
        if (s != null) System.out.println(s.value() + "  " + m.getName());
    }
}
```

> Real frameworks (Jackson, JPA, Spring) do this for every class they
> process — read fields, check annotations, decide what to serialize or
> persist. The `mvn spring-boot:run` command in Module 02 starts a *much*
> larger version of this same pattern.
