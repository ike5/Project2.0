package com.example.payments;

public record CashPayment(long amountCents, String currency) implements Payment {
    public CashPayment {
        if (amountCents <= 0) throw new IllegalArgumentException("amount must be > 0");
        if (currency == null) throw new IllegalArgumentException("currency required");
    }
    @Override public String kind() { return "cash"; }
}
