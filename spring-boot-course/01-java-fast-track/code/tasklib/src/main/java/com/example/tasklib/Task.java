package com.example.tasklib;

import java.time.Instant;

public record Task(long id, String title, boolean done, Instant createdAt) {
    public Task {
        if (title == null || title.isBlank())
            throw new IllegalArgumentException("title is required");
    }
}
