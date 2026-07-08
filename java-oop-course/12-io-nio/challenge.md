# Challenge 12 — I/O, NIO.2 & Serialization

Solution in [`solutions/`](./solutions/). Try first.

## Tasks

1. **`copyDir` with `Files.walk`.** Write `static Path copyDir(Path src,
   Path dst)` that recursively copies a directory tree. Use `Files.walk`
   on the source and create files/dirs at the destination with
   `Files.createDirectories` and `Files.copy`.

2. **Word count on a large file.** Write `static Map<String, Long>
   wordCount(Path path)` that opens the file with `Files.lines`,
   tokenises on non-letter characters, lower-cases, and counts. Don't
   load the whole file into memory.

3. **`Properties` round-trip.** Build a `Map<String, String>` of three
   settings, write them to a temp `Properties` file, read them back,
   and confirm the round trip.

4. **A custom `AutoCloseable` that logs on close.** Write
   `class LoggingReader implements AutoCloseable` that wraps an
   `InputStream`, delegates `read` to it, and prints a "closing"
   message in `close()`. Use it inside `try (...)` in a `main` to read
   a small file.

5. **Demonstrate the `transient` field.** Create a `record User(String
   name, int age) implements Serializable` (with
   `serialVersionUID`), mark `age` as `transient`, serialise and
   deserialise, and confirm that the deserialised object's `age` is
   `0` (the default for missing `transient` int).

## Success criteria

- [ ] `copyDir` produces a faithful tree, including subdirectories and
      empty directories.
- [ ] `wordCount` works on a multi-MB file without blowing up memory.
- [ ] The `Properties` round trip yields identical key/value pairs.
- [ ] `LoggingReader` logs when closed.
- [ ] The `transient` field is zero after deserialisation.
