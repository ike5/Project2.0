# Challenge 10 — Annotations, Reflection & Modern Sugar

Solution in [`solutions/`](./solutions/). Try first.

## Tasks

1. **A `@JsonField` annotation.** Build an annotation `@JsonField` that
   is `@Target(FIELD)`, `@Retention(RUNTIME)`, and accepts a `String
   name()` (default = the field's name). Mark up a `record User(String
   username, @JsonField(name = "email_address") String email)`. Write a
   small reflection routine that prints the JSON-like representation
   `{"name": value, ...}` honouring `@JsonField`.

2. **A `@Command` annotation processor.** Build `@Command("name")` and a
   `CommandRunner` that, given a class, finds every method with
   `@Command`, prints the registered names, and invokes the chosen one.
   (Bonus: support a `@Help` element on the annotation.)

3. **A JSON-style configuration loader using text blocks.** Write
   `Map<String, String> parseSimpleConfig(String text)` that handles lines
   of the form `key = value`, ignoring blanks and `#` comments. Pass in
   a text-block string. Use `var` where it helps.

4. **Reflection: list public methods of a class.** Write
   `List<String> methodNames(Class<?> c)` that returns the names of
   every public method declared on `c` (no `Object` methods like
   `toString`, `equals`, etc.). Use `getDeclaredMethods()` and
   filter.

5. **`var` vs. explicit types.** For a small main, write five local
   variables with `var` and the same five with explicit types. Compile
   both; confirm the bytecode is identical with `javap -c -p`. (Hint:
   `javap -c -p out/com/example/.../Main.class`.)

## Success criteria

- [ ] `@JsonField` is honoured by the JSON printer.
- [ ] `@Command` is found by reflection and dispatched.
- [ ] The config loader handles comments and blank lines.
- [ ] `methodNames(Class)` excludes `Object`'s methods.
- [ ] `javap` shows the same bytecode for `var` and explicit types.
