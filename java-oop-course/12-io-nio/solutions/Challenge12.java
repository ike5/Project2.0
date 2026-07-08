package com.example.files;

import java.io.IOException;
import java.io.InputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.OutputStream;
import java.io.Serializable;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;
import java.util.stream.Stream;

public final class Challenge12 {

    private Challenge12() {}

    public static void main(String[] args) throws Exception {
        // 1. copyDir.
        Path src = Path.of("/tmp/oop12-src");
        Path dst = Path.of("/tmp/oop12-dst");
        setupTree(src);
        copyDir(src, dst);
        System.out.println("copied: " + Files.walk(dst).count() + " entries");

        // 2. wordCount.
        Path wc = Path.of("/tmp/oop12-text.txt");
        Files.writeString(wc, "the quick brown fox jumps over the lazy dog the dog barks");
        System.out.println("wordCount = " + wordCount(wc).get("the"));

        // 3. Properties round-trip.
        Path propsPath = Path.of("/tmp/oop12.properties");
        Map<String, String> in = new HashMap<>();
        in.put("host", "localhost");
        in.put("port", "8080");
        in.put("user", "ada");
        writeProperties(in, propsPath);
        System.out.println("round trip = " + readProperties(propsPath));

        // 4. LoggingReader.
        Path file = Path.of("/tmp/oop12-text.txt");
        try (var r = new LoggingReader(Files.newInputStream(file))) {
            System.out.println("read " + r.readAllBytes().length + " bytes");
        }

        // 5. transient field.
        var u = new User("Ada", 36);
        Path bin = Path.of("/tmp/oop12-user.bin");
        try (var out = new ObjectOutputStream(Files.newOutputStream(bin))) {
            out.writeObject(u);
        }
        try (var ois = new ObjectInputStream(Files.newInputStream(bin))) {
            User back = (User) ois.readObject();
            System.out.println("deserialised: " + back + " (age is transient -> " + back.age() + ")");
        }
    }

    // 1. copyDir.
    public static void copyDir(Path src, Path dst) throws IOException {
        try (Stream<Path> walk = Files.walk(src)) {
            walk.forEach(p -> {
                try {
                    Path target = dst.resolve(src.relativize(p).toString());
                    if (Files.isDirectory(p)) {
                        Files.createDirectories(target);
                    } else {
                        Files.copy(p, target);
                    }
                } catch (IOException e) {
                    throw new RuntimeException(e);
                }
            });
        }
    }

    private static void setupTree(Path root) throws IOException {
        if (Files.exists(root)) {
            try (var walk = Files.walk(root)) { walk.forEach(p -> p.toFile().delete()); }
            Files.deleteIfExists(root);
        }
        Files.createDirectories(root.resolve("a/b"));
        Files.writeString(root.resolve("a/file1.txt"), "one");
        Files.writeString(root.resolve("a/b/file2.txt"), "two");
    }

    // 2. wordCount.
    public static Map<String, Long> wordCount(Path path) throws IOException {
        Map<String, Long> counts = new HashMap<>();
        try (var lines = Files.lines(path, StandardCharsets.UTF_8)) {
            lines.flatMap(s -> Stream.of(s.toLowerCase().split("[^a-z0-9]+")))
                 .filter(w -> !w.isEmpty())
                 .forEach(w -> counts.merge(w, 1L, Long::sum));
        }
        return counts;
    }

    // 3. Properties.
    public static void writeProperties(Map<String, String> map, Path path) throws IOException {
        Properties p = new Properties();
        p.putAll(map);
        try (OutputStream out = Files.newOutputStream(path)) {
            p.store(out, "config");
        }
    }
    public static Map<String, String> readProperties(Path path) throws IOException {
        Properties p = new Properties();
        try (InputStream in = Files.newInputStream(path)) {
            p.load(in);
        }
        Map<String, String> out = new HashMap<>();
        for (String k : p.stringPropertyNames()) out.put(k, p.getProperty(k));
        return out;
    }

    // 4. LoggingReader.
    public static final class LoggingReader implements AutoCloseable {
        private final InputStream in;
        public LoggingReader(InputStream in) { this.in = in; }
        public int read() throws IOException { return in.read(); }
        public int read(byte[] b, int off, int len) throws IOException { return in.read(b, off, len); }
        public byte[] readAllBytes() throws IOException { return in.readAllBytes(); }
        @Override public void close() throws IOException {
            System.out.println("[logger] closing");
            in.close();
        }
    }

    // 5. Serializable with a transient field. Records can't mark a
    //    component as transient directly, so we use a class.
    public static final class User implements Serializable {
        @java.io.Serial private static final long serialVersionUID = 1L;
        private final String name;
        private transient int age;
        public User(String name, int age) { this.name = name; this.age = age; }
        public String name() { return name; }
        public int age()     { return age; }
        @Override public String toString() { return "User[" + name + ", " + age + "]"; }
    }
}
