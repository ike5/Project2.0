package com.example.tasklib;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicLong;

public class TaskStore {
    private final Map<Long, Task> byId = new LinkedHashMap<>();
    private final AtomicLong nextId = new AtomicLong(1);

    public Task create(String title) {
        Task t = new Task(nextId.getAndIncrement(), title, false, Instant.now());
        byId.put(t.id(), t);
        return t;
    }

    public Optional<Task> findById(long id) {
        return Optional.ofNullable(byId.get(id));
    }

    public List<Task> findOpen() {
        return byId.values().stream().filter(t -> !t.done()).toList();
    }

    public List<Task> findByTitleContains(String fragment) {
        String f = fragment.toLowerCase();
        return byId.values().stream()
            .filter(t -> t.title().toLowerCase().contains(f))
            .toList();
    }

    public boolean markDone(long id) {
        Task t = byId.get(id);
        if (t == null) return false;
        byId.put(id, new Task(t.id(), t.title(), true, t.createdAt()));
        return true;
    }
}
