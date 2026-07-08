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
