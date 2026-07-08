package com.example.files;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class Main {
    public static void main(String[] args) throws IOException {
        Path log = Path.of("data/sample.log");
        Files.createDirectories(log.getParent());
        Files.writeString(log, """
                INFO  app started
                WARN  deprecated method called
                ERROR something bad happened
                INFO  request handled
                DEBUG retrying
                ERROR another bad thing
                """);

        var entries = LogIndex.parse(log);
        System.out.println("entries: " + entries);
        System.out.println("counts: " + LogIndex.countByLevel(entries));

        try (var walk = Files.walk(Path.of("out").toAbsolutePath())) {
            long javaCount = walk.filter(p -> p.toString().endsWith(".class")).count();
            System.out.println("class files: " + javaCount);
        }
    }
}
