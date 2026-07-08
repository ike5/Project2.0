# Lab 01 — Java Fluency in One File

**You'll:** build a small Maven project with one class that exercises records,
collections, streams, lambdas, `Optional`, exceptions, and a custom annotation
reader. The class will be a tiny in-memory "task store" you can extend in
Module 02.

⏱️ ~50 min. Run from `spring-boot-course/01-java-fast-track`.

---

## Part A — Scaffold a Maven project

Create the folder structure and `pom.xml`:

```bash
mkdir -p code/tasklib/src/main/java/com/example/tasklib
cd code/tasklib
```

`pom.xml` (a minimal Maven project — no Spring yet):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>tasklib</artifactId>
  <version>0.0.1-SNAPSHOT</version>
  <properties>
    <maven.compiler.source>21</maven.compiler.source>
    <maven.compiler.target>21</maven.compiler.target>
  </properties>
</project>
```

✅ **Checkpoint:** `mvn compile` runs without errors.

---

## Part B — Records + a tiny store

Create `src/main/java/com/example/tasklib/Task.java`:
```java
package com.example.tasklib;
import java.time.Instant;

public record Task(long id, String title, boolean done, Instant createdAt) {
    public Task {
        if (title == null || title.isBlank())
            throw new IllegalArgumentException("title is required");
    }
}
```

> The compact constructor (`public Task { ... }`) lets you validate fields
> without writing the full signature.

Create `src/main/java/com/example/tasklib/TaskStore.java`:
```java
package com.example.tasklib;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;

public class TaskStore {
    private final Map<Long, Task> byId = new LinkedHashMap<>();
    private final AtomicLong nextId = new AtomicLong(1);

    public Task create(String title) {
        Task t = new Task(nextId.getAndIncrement(), title, false, Instant.now());
        byId.put(t.id(), t);
        return t;
    }

    public Optional<Task> findById(long id) { return Optional.ofNullable(byId.get(id)); }

    public List<Task> findOpen() {
        return byId.values().stream().filter(t -> !t.done()).toList();
    }

    public List<Task> findByTitleContains(String fragment) {
        String f = fragment.toLowerCase();
        return byId.values().stream()
            .filter(t -> t.title().toLowerCase().contains(f))
            .toList();
    }

    public boolean markDone(long id) {
        Task t = byId.get(id);
        if (t == null) return false;
        byId.put(id, new Task(t.id(), t.title(), true, t.createdAt()));
        return true;
    }
}
```

`mvn compile` ✅ compiles.

---

## Part C — A `main` method that exercises it

Create `src/main/java/com/example/tasklib/Demo.java`:
```java
package com.example.tasklib;
import java.util.List;

public class Demo {
    public static void main(String[] args) {
        TaskStore store = new TaskStore();
        store.create("Buy milk");
        store.create("Fix login bug");
        store.create("Write docs");
        store.markDone(2);

        System.out.println("== all ==");
        store.findById(1).ifPresent(System.out::println);
        System.out.println(store.findById(99).orElseThrow());

        System.out.println("\n== open ==");
        List<Task> open = store.findOpen();
        open.forEach(System.out::println);

        System.out.println("\n== search 'log' ==");
        store.findByTitleContains("log").forEach(System.out::println);

        try {
            store.create("   ");
        } catch (IllegalArgumentException e) {
            System.out.println("\ncaught: " + e.getMessage());
        }
    }
}
```

Run it:
```bash
mvn -q compile exec:java -Dexec.mainClass=com.example.tasklib.Demo
# (if you don't have the exec plugin, just `java -cp target/classes com.example.tasklib.Demo`)
```

✅ Expected: the records print with `Task[id=..., title=..., ...]`, the open
list excludes the marked-done one, the search returns "Fix login bug", and
the blank-title `create` throws and is caught.

> **What just happened:** records (Task), generics (`Map<Long, Task>`,
> `Optional<Task>`), lambdas (`t -> !t.done()`), streams (`.stream()
> .filter(...).toList()`), method references (`System.out::println`),
> `Optional` chaining, and a custom checked-style validation in a compact
> constructor — all in one ~50-line file.

---

## Part D — A custom annotation + reflection

Spring reads annotations at runtime. Try it yourself.

Create `src/main/java/com/example/tasklib/JsonField.java`:
```java
package com.example.tasklib;
import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface JsonField {
    String name() default "";
}
```

Annotate `Task`'s fields (temporarily) — actually, since `Task` is a record
with final components, add a separate example class:
```java
package com.example.tasklib;
import java.util.stream.Collectors;
import java.lang.reflect.Field;

public class Demo2 {
    record Person(@JsonField(name = "full_name") String name, int age) {}

    public static void main(String[] args) throws Exception {
        Person p = new Person("Ann", 30);
        String json = toJson(p);
        System.out.println(json);   // {"full_name":"Ann","age":30}
    }

    static String toJson(Object o) throws IllegalAccessException {
        var fields = o.getClass().getDeclaredFields();
        return fields.stream().map(f -> {
            f.setAccessible(true);
            String key = f.isAnnotationPresent(JsonField.class)
                ? f.getAnnotation(JsonField.class).name()
                : f.getName();
            try {
                Object v = f.get(o);
                String val = v instanceof String s ? "\"" + s + "\"" : String.valueOf(v);
                return "\"" + key + "\":" + val;
            } catch (IllegalAccessException e) { throw new RuntimeException(e); }
        }).collect(Collectors.joining(",", "{", "}"));
    }
}
```

Run it: `mvn -q compile exec:java -Dexec.mainClass=com.example.tasklib.Demo2`

✅ Expected: `{"full_name":"Ann","age":30}`.

> **Why this matters:** Spring's `@RequestBody`, `@RestController`, and JPA's
> `@Entity` all work exactly like this — annotations on your classes that
> frameworks read at runtime to generate code (JSON parsers, SQL queries, etc.).

---

## What you learned

- A Java program is a class with a `main(String[])` method.
- Records give you immutable data classes with one line of code.
- The Stream API turns loops into readable pipelines.
- `Optional` replaces `null` checks at the API boundary.
- Custom annotations + reflection is how frameworks (and Spring) work.
- Maven is the build tool; `mvn compile` / `mvn package` / `java -jar` are
  the three commands you'll use hundreds of times.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 02](../02-spring-boot-fundamentals/).
