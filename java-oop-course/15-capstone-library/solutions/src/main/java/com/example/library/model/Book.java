package com.example.library.model;

import java.util.Objects;

public record Book(String isbn, String title, String author) {
    public Book {
        Objects.requireNonNull(isbn, "isbn");
        Objects.requireNonNull(title, "title");
        Objects.requireNonNull(author, "author");
        if (isbn.isBlank()) throw new IllegalArgumentException("isbn must not be blank");
    }
}
