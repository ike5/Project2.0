package com.example.library.model;

import java.util.Objects;

public record Member(long id, String name, String email) {
    public Member {
        Objects.requireNonNull(name, "name");
        Objects.requireNonNull(email, "email");
        if (name.isBlank()) throw new IllegalArgumentException("name must not be blank");
        if (!email.contains("@")) throw new IllegalArgumentException("email invalid");
    }
}
