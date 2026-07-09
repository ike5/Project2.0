package com.example.patterns;

import java.util.Objects;

public record Order(long id, String customer, long baseCents, long finalCents) {
    public Order {
        if (id <= 0) throw new IllegalArgumentException("id > 0");
        Objects.requireNonNull(customer, "customer");
        if (baseCents < 0) throw new IllegalArgumentException("baseCents >= 0");
    }

    public Order apply(PricingStrategy strategy) {
        return new Order(id, customer, baseCents, strategy.price(baseCents));
    }

    public static Builder builder() { return new Builder(); }

    public static final class Builder {
        private long id;
        private String customer;
        private long baseCents;
        public Builder id(long id)              { this.id = id; return this; }
        public Builder customer(String c)      { this.customer = c; return this; }
        public Builder baseCents(long b)       { this.baseCents = b; return this; }
        public Order build()                    { return new Order(id, customer, baseCents, baseCents); }
    }
}
