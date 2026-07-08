package com.example.payments;

public record ZeroPayment(String currency) implements Payment {
    public ZeroPayment {
        if (currency == null) throw new IllegalArgumentException("currency required");
    }
    @Override public long amountCents() { return 0; }
    @Override public String kind() { return "zero"; }
}
