# Lab 10 — Annotations, Reflection & Modern Sugar

**You'll:** define a custom annotation, write a tiny processor that reads
it via reflection, and exercise `var` and text blocks. ⏱️ ~40 min.

---

## Part A — Set up

```bash
mkdir -p ~/dev/oop10 && cd ~/dev/oop10
mkdir -p src/com/example/plugins
```

## Part B — A `@Timed` annotation

`src/com/example/plugins/Timed.java`:
```java
package com.example.plugins;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Timed {
    String unit() default "ms";
}
```

## Part C — A class with `@Timed` methods

`src/com/example/plugins/Service.java`:
```java
package com.example.plugins;

public final class Service {
    @Timed
    public String fastOp() { return "fast"; }

    @Timed(unit = "ns")
    public String slowerOp() throws InterruptedException {
        Thread.sleep(5);
        return "slow";
    }

    public String unTimed() { return "untracked"; }
}
```

## Part D — A processor that invokes every `@Timed` method

`src/com/example/plugins/Processor.java`:
```java
package com.example.plugins;

import java.lang.reflect.Method;

public final class Processor {
    public static void run(Object target) throws Exception {
        for (Method m : target.getClass().getDeclaredMethods()) {
            Timed t = m.getAnnotation(Timed.class);
            if (t == null) continue;
            long start = System.nanoTime();
            Object result = m.invoke(target);
            long elapsed = switch (t.unit()) {
                case "ns" -> System.nanoTime() - start;
                case "us" -> (System.nanoTime() - start) / 1_000;
                default   -> (System.nanoTime() - start) / 1_000_000;
            };
            System.out.printf("[%s] %s.%s -> %s (took %d %s)%n",
                    t.unit(), target.getClass().getSimpleName(), m.getName(),
                    result, elapsed, t.unit());
        }
    }
}
```

## Part E — Driver with `var` and a text block

`src/com/example/plugins/Main.java`:
```java
package com.example.plugins;

public class Main {
    public static void main(String[] args) throws Exception {
        var service = new Service();
        Processor.run(service);

        // Text block + var in action.
        var banner = """
                +--------------------+
                |  Annotation runner |
                +--------------------+""";
        System.out.println(banner);
    }
}
```

Compile + run:
```bash
javac -d out $(find src -name '*.java')
java -cp out com.example.plugins.Main
```

Expected (timing will vary):
```
[ms] Service.fastOp -> fast (took 0 ms)
[ns] Service.slowerOp -> slow (took 5000000 ns)
+--------------------+
|  Annotation runner |
+--------------------+
```

✅ Notice the runtime polymorphism: the same `Processor` finds every
`@Timed` method on any class, with no per-class code.

## Part F — `var` discipline

Try these in a small `main`:
```java
var a = 42;            // int
var b = 42L;           // long
var c = 3.14;          // double
var d = "hi";          // String
var e = List.of(1, 2); // List<Integer>
```

`var` infers the *static* type — the compiler still produces the same
bytecode. It's purely a readability win.

## Part G — Helpful NPE

In Java 21+, write a small NPE and look at the message:
```java
String s = null;
System.out.println(s.length());
```

The error message should tell you **"Cannot invoke 'String.length()'
because 's' is null"** — the variable name appears. (In older JVMs the
message is just the line number.)

## What you learned

- Annotations are typed markers; meta-annotations (`@Retention`,
  `@Target`) control where and when they're available.
- Reflection reads `RUNTIME` annotations — slow, fragile, but useful for
  frameworks.
- `var` is local type inference, not dynamic typing.
- Text blocks make JSON, SQL, and HTML literals readable.

➡️ **[challenge.md](./challenge.md)** then [Module 11](../11-concurrency/).
