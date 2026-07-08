package com.example.plugins;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.RecordComponent;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class Challenge10 {

    private Challenge10() {}

    public static void main(String[] args) throws Exception {
        // 1. @JsonField on a record.
        var user = new User("ada", "ada@example.com");
        System.out.println(toJson(user));

        // 2. @Command on a service.
        CommandRunner.printCommands(new GreetService());
        CommandRunner.invoke(new GreetService(), "hello");

        // 3. Simple config with text block.
        var conf = parseSimpleConfig("""
                # example config
                host = localhost
                port = 8080

                # trailing
                """);
        System.out.println(conf);

        // 4. methodNames excluding Object.
        System.out.println(methodNames(GreetService.class));

        // 5. var vs. explicit — see README. javap shows identical bytecode.
    }

    // 1. @JsonField + record.
    @Target(ElementType.RECORD_COMPONENT)
    @Retention(RetentionPolicy.RUNTIME)
    public @interface JsonField {
        String name() default "";
    }

    public record User(@JsonField String username, @JsonField(name = "email_address") String email) {}

    public static String toJson(Object o) throws Exception {
        Map<String, String> map = new LinkedHashMap<>();
        if (o.getClass().isRecord()) {
            for (RecordComponent rc : o.getClass().getRecordComponents()) {
                JsonField ann = rc.getAnnotation(JsonField.class);
                if (ann == null) continue;
                String name = ann.name().isEmpty() ? rc.getName() : ann.name();
                map.put(name, String.valueOf(rc.getAccessor().invoke(o)));
            }
        } else {
            for (Field f : o.getClass().getDeclaredFields()) {
                f.setAccessible(true);
                JsonField ann = f.getAnnotation(JsonField.class);
                if (ann == null) continue;
                String name = ann.name().isEmpty() ? f.getName() : ann.name();
                map.put(name, String.valueOf(f.get(o)));
            }
        }
        StringBuilder sb = new StringBuilder("{");
        var it = map.entrySet().iterator();
        while (it.hasNext()) {
            var e = it.next();
            sb.append("\"").append(e.getKey()).append("\": \"").append(e.getValue()).append("\"");
            if (it.hasNext()) sb.append(", ");
        }
        return sb.append("}").toString();
    }

    // 2. @Command processor.
    @Target(ElementType.METHOD)
    @Retention(RetentionPolicy.RUNTIME)
    public @interface Command {
        String value();
        String help() default "";
    }

    public static final class GreetService {
        @Command(value = "hello", help = "print a greeting")
        public String hello() { return "hi"; }

        @Command(value = "bye",   help = "print a farewell")
        public String bye()   { return "see ya"; }
    }

    public static final class CommandRunner {
        public static void printCommands(Object target) {
            for (Method m : target.getClass().getDeclaredMethods()) {
                Command c = m.getAnnotation(Command.class);
                if (c != null) System.out.println("  " + c.value() + " — " + c.help());
            }
        }
        public static Object invoke(Object target, String name) throws Exception {
            for (Method m : target.getClass().getDeclaredMethods()) {
                Command c = m.getAnnotation(Command.class);
                if (c != null && c.value().equals(name)) {
                    return m.invoke(target);
                }
            }
            throw new IllegalArgumentException("no such command: " + name);
        }
    }

    // 3. simple config parser.
    public static Map<String, String> parseSimpleConfig(String text) {
        Map<String, String> out = new LinkedHashMap<>();
        for (String raw : text.lines().map(String::strip).toList()) {
            if (raw.isEmpty() || raw.startsWith("#")) continue;
            int eq = raw.indexOf('=');
            if (eq < 0) continue;
            out.put(raw.substring(0, eq).strip(), raw.substring(eq + 1).strip());
        }
        return out;
    }

    // 4. methodNames excluding Object.
    public static List<String> methodNames(Class<?> c) {
        List<String> names = new ArrayList<>();
        for (Method m : c.getDeclaredMethods()) {
            if (java.lang.reflect.Modifier.isPublic(m.getModifiers())) {
                names.add(m.getName());
            }
        }
        return names.stream().filter(n -> !isObjectMethod(n)).toList();
    }
    private static boolean isObjectMethod(String n) {
        return Arrays.asList("toString", "equals", "hashCode", "getClass", "wait", "notify", "notifyAll", "clone").contains(n);
    }
}
