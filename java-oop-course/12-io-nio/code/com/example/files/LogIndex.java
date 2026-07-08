package com.example.files;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

public final class LogIndex {
    private LogIndex() {}

    public static List<Entry> parse(Path log) throws IOException {
        try (var lines = Files.lines(log)) {
            return lines
                .filter(s -> !s.isBlank())
                .map(LogIndex::parseLine)
                .filter(Objects::nonNull)
                .toList();
        }
    }

    public static Entry parseLine(String line) {
        int sp = line.indexOf(' ');
        if (sp <= 0) return null;
        return new Entry(line.substring(0, sp), line.substring(sp + 1).trim());
    }

    public static Map<String, Long> countByLevel(List<Entry> entries) {
        return entries.stream().collect(Collectors.groupingBy(
                Entry::level, Collectors.counting()));
    }
}
