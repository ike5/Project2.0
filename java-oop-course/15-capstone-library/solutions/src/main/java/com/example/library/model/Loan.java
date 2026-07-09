package com.example.library.model;

import java.time.LocalDate;
import java.util.Objects;

public record Loan(long id, Book book, Member member, LocalDate borrowedOn, LocalDate dueOn) {
    public Loan {
        Objects.requireNonNull(book, "book");
        Objects.requireNonNull(member, "member");
        Objects.requireNonNull(borrowedOn, "borrowedOn");
        Objects.requireNonNull(dueOn, "dueOn");
        if (dueOn.isBefore(borrowedOn)) throw new IllegalArgumentException("dueOn before borrowedOn");
    }
}
