package com.example.orders;

import java.time.Instant;
import java.util.List;

public record Order(long id, String customer, List<String> items, long totalCents, Instant placedAt) {
    public Order {
        items = List.copyOf(items);
    }
}
