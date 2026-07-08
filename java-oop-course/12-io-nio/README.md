# Module 12 — I/O, NIO.2 & Serialization

**Goal:** work with the modern file APIs (`Path`, `Files`, streams of
lines), know when to reach for `ObjectInputStream` vs. a JSON library,
and avoid the common pitfalls of each.

⏱️ ~2 h · 🎯 Prereq: Module 11.

---

## 1. The two I/O worlds

Java has two file I/O stacks:

- **`java.io`** — the classic streams and `File`. Still works; mostly
  superseded.
- **`java.nio.file`** (a.k.a. NIO.2) — the modern API. Use this for
  anything new.

In practice, "modern Java I/O" means **`Path` + `Files`**.

## 2. `Path` — the modern file

```java
Path p = Path.of("/tmp", "hello.txt");     // platform-independent join
Path home = Path.of(System.getProperty("user.home"));
Path child = home.resolve("projects").resolve("readme.md");
Path sibling = p.resolveSibling("other.txt");
Path normalized = Path.of("./a/./b/../c").normalize();   // "a/c"
```

`Path` is *immutable*; every method returns a new `Path`. To actually
interact with the filesystem, use `Files`.

## 3. `Files` — the workhorse

```java
// Read all bytes
byte[] data = Files.readAllBytes(path);

// Read all lines
List<String> lines = Files.readAllLines(path);

// Read a string (whole file)
String text = Files.readString(path, StandardCharsets.UTF_8);

// Write a string
Files.writeString(path, "Hello\n", StandardCharsets.UTF_8);

// Copy / move / delete
Files.copy(src, dst, StandardCopyOption.REPLACE_EXISTING);
Files.move(src, dst);
Files.delete(path);          // throws if missing
boolean deleted = Files.deleteIfExists(path);   // returns whether anything happened

// Attributes
long size  = Files.size(path);
FileTime modified = Files.getLastModifiedTime(path);
boolean isDir = Files.isDirectory(path);
```

The most-used operations are all here. For "I just need to read a
file," `Files.readString` is the right answer.

## 4. `Files.lines(path)` — stream of lines

```java
try (var lines = Files.lines(path)) {
    long count = lines.filter(s -> !s.isBlank()).count();
}
```

The returned `Stream<String>` is closed by `try`-with-resources.
Combine with all the stream operations you know.

## 5. Walking a directory tree

```java
try (var stream = Files.walk(root)) {
    List<Path> javaFiles = stream
        .filter(p -> p.toString().endsWith(".java"))
        .toList();
}
```

For *shallow* iteration, use `Files.list` (no recursion). For
*configurable* depth, use `Files.walk(path, depth)`. For *lazy* DFS
with filters, use `Files.find`.

## 6. `BufferedReader` and `BufferedWriter` for streaming I/O

When the file is large, you don't want to load it all into memory:

```java
try (var reader = Files.newBufferedReader(path);
     var writer = Files.newBufferedWriter(target)) {
    String line;
    while ((line = reader.readLine()) != null) {
        writer.write(line.toUpperCase());
        writer.newLine();
    }
}
```

The `reader.transferTo(writer)` shortcut (Java 10+) is even simpler.

## 7. The classic `java.io` streams

You will still meet them in libraries and legacy code:

```java
try (var in  = new FileInputStream("a.bin");
     var out = new FileOutputStream("b.bin")) {
    in.transferTo(out);
}
```

`InputStream` / `OutputStream` for bytes, `Reader` / `Writer` for
characters. The rule: **always wrap with a `Buffered*` variant** for
performance. The `Files` helpers do this for you.

## 8. `AutoCloseable` and `try`-with-resources

Everything above (`InputStream`, `OutputStream`, `Reader`, `Writer`,
`Path`, `DirectoryStream`, `Stream<Path>`) implements `AutoCloseable`.
Use `try (...)` and stop worrying about leaks.

## 9. Serialization — `Serializable`

The classic Java object-to-bytes mechanism:

```java
class User implements Serializable {
    @java.io.Serial private static final long serialVersionUID = 1L;
    private final String name;
    /* ... */
}

try (var out = new ObjectOutputStream(new FileOutputStream("user.bin"))) {
    out.writeObject(user);
}
try (var in = new ObjectInputStream(new FileInputStream("user.bin"))) {
    User u = (User) in.readObject();
}
```

**Caveats:**
- **Versioning** — `serialVersionUID` is your handle to "this is the same
  class as before." If you change fields, you'll need to bump it.
- **Security** — `ObjectInputStream` deserialises arbitrary classes.
  This is the source of dozens of CVEs. **Never deserialise untrusted
  bytes.**
- **Performance** — slow, verbose, binary. JSON is usually better.
- **`transient`** fields are skipped — useful for caches and
  derived data.

For new code, **prefer JSON** (Jackson, Gson) or **Protocol Buffers**.

## 10. JSON with Jackson (the easy way)

If you can pull in a dependency, Jackson is the de facto standard. From
a single `ObjectMapper`:

```java
ObjectMapper mapper = new ObjectMapper();
String json = mapper.writeValueAsString(user);
User u = mapper.readValue(json, User.class);
```

Jackson works with records, immutable classes, and `Optional`. It uses
reflection, so it's slow on hot paths — but the *right answer* for
"convert a Java object to/from JSON."

The course doesn't add Jackson as a dependency to keep the labs
self-contained, but you'll see it in real code.

## 11. The `transient` keyword

A `transient` field is *skipped* during default `Serializable`:
```java
class User implements Serializable {
    private final String name;
    private transient long lastAccess;     // not serialised
}
```
Use it for caches, locks, derived data, and any field that doesn't make
sense across processes.

## 12. Properties files

`java.util.Properties` is the tiny `Map<String, String>` for config:

```java
var props = new Properties();
try (var r = Files.newBufferedReader(Path.of("config.properties"))) {
    props.load(r);
}
String host = props.getProperty("host", "localhost");
```

Properties files are `key=value`, with `#` comments. `Properties.load`
parses them; `Properties.store` writes them.

## 13. Watch service (preview)

`java.nio.file.WatchService` lets you watch a directory for changes. It's
useful for "rebuild when source changes" tools. We don't use it in this
course, but it's worth knowing it exists.

## 14. A worked example — line-counter

```java
public static long countLines(Path path) throws IOException {
    try (var lines = Files.lines(path)) {
        return lines.filter(s -> !s.isBlank()).count();
    }
}
```

This is the *whole* implementation. `Files.lines` gives you a stream of
strings, the filter ignores blanks, and `.count()` runs the pipeline.
The `try`-with-resources closes the underlying file handle.

## 15. A bigger example — a tiny "log indexer"

```java
record Entry(String level, String message) {}

List<Entry> parse(Path log) throws IOException {
    try (var lines = Files.lines(log)) {
        return lines
            .filter(s -> !s.isBlank())
            .map(LogIndex::parseLine)
            .filter(Objects::nonNull)
            .toList();
    }
}

static Entry parseLine(String line) {
    // "ERROR something bad happened" -> Entry("ERROR", "something bad happened")
    int sp = line.indexOf(' ');
    if (sp < 0) return null;
    return new Entry(line.substring(0, sp), line.substring(sp + 1));
}
```

Notice the layering: `parse` is the high-level operation; `parseLine`
is a static helper. Records for the data, stream pipeline for the
composition, `try`-with-resources for safety.

---

## Do the lab

Build a small "log indexer" that reads a file, parses lines, and
groups by level. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

`Path` · `Paths` · `Files` · `readString` / `writeString` · `readAllLines`
/ `write` · `Files.lines` · `Files.walk` / `Files.list` / `Files.find` ·
`BufferedReader` / `BufferedWriter` · `InputStream` / `OutputStream` ·
`Reader` / `Writer` · `AutoCloseable` · `try`-with-resources ·
`Serializable` · `serialVersionUID` · `transient` · `ObjectInputStream` /
`ObjectOutputStream` · `Properties`

**Next →** [Module 13: Modules (JPMS) & Packaging](../13-modules-jpms/)
