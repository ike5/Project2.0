package com.example.parser;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicLong;

public final class Challenge08 {

    private Challenge08() {}

    public static void main(String[] args) throws Exception {
        // 1. CSV read.
        Path csv = Path.of("/tmp/oop08.csv");
        Files.writeString(csv, """
                a,b,c
                1,2,3
                4,5,6
                """);
        System.out.println(readCsv(csv));

        // 2. requirePositive.
        try { MathService.requirePositive(0); }
        catch (ServiceException e) { System.out.println("rejected: " + e.getMessage() + " (cause: " + e.getCause() + ")"); }

        // 3. findUserByEmail chain.
        var users = List.of(
                new User(1, "ada@example.com",  Optional.of(new Address("JP"))),
                new User(2, "grace@example.com", Optional.empty()));
        Optional<String> country = findUserByEmail(users, "ada@example.com")
                .flatMap(User::address)
                .map(Address::country);
        System.out.println("ada's country: " + country.orElse("(none)"));

        // 4. Timer.
        try (var t = new Timer("read")) {
            Thread.sleep(120);
        }

        // 5. Uncaught handler.
        Thread.setDefaultUncaughtExceptionHandler((t, e) ->
                System.out.println("[handler] thread=" + t.getName() + " ex=" + e));
        if (args.length == 0) {
            throw new RuntimeException("kaboom");
        }
    }

    // 1. CSV reader.
    public static List<List<String>> readCsv(Path path) throws IOException {
        List<List<String>> rows = new ArrayList<>();
        try (BufferedReader r = Files.newBufferedReader(path)) {
            String line;
            while ((line = r.readLine()) != null) {
                if (line.isBlank()) continue;
                rows.add(Arrays.asList(line.split(",")));
            }
        }
        return rows;
    }

    // 2. MathService.
    public static final class MathService {
        public static int requirePositive(int x) throws ServiceException {
            try {
                if (x <= 0) throw new IllegalArgumentException("must be positive: " + x);
                return x;
            } catch (IllegalArgumentException e) {
                throw new ServiceException("non-positive: " + x, e);
            }
        }
    }

    // 3. findUserByEmail.
    public record User(int id, String email, Optional<Address> address) {}
    public record Address(String country) {}
    public static Optional<User> findUserByEmail(List<User> users, String email) {
        return users.stream().filter(u -> u.email().equals(email)).findFirst();
    }

    // 4. Timer.
    public static final class Timer implements AutoCloseable {
        private final String label;
        private final long startNanos;
        public Timer(String label) {
            this.label = label;
            this.startNanos = System.nanoTime();
        }
        @Override public void close() {
            long elapsedMs = (System.nanoTime() - startNanos) / 1_000_000;
            System.out.println("[timer] " + label + " took " + elapsedMs + " ms");
        }
    }
}
