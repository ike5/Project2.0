package com.example.payments;

public record BankTransfer(long amountCents, String currency, String from) implements Payment {
    public BankTransfer {
        if (amountCents <= 0) throw new IllegalArgumentException("amount must be > 0");
        if (currency == null) throw new IllegalArgumentException("currency required");
        if (from == null || from.isBlank()) throw new IllegalArgumentException("from required");
    }
    @Override public String kind() { return "transfer"; }
}
