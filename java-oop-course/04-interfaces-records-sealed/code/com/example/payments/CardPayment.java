package com.example.payments;

public record CardPayment(long amountCents, String currency, String last4) implements Payment {
    public CardPayment {
        if (amountCents <= 0) throw new IllegalArgumentException("amount must be > 0");
        if (currency == null || currency.isBlank()) throw new IllegalArgumentException("currency required");
        if (last4 == null || last4.length() != 4) throw new IllegalArgumentException("last4 required");
    }
    @Override public String kind() { return "card"; }
}
