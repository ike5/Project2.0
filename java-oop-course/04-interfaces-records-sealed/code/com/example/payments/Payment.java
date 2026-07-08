package com.example.payments;

public sealed interface Payment
        permits CardPayment, CashPayment, BankTransfer, ZeroPayment {

    long amountCents();
    String currency();
    String kind();

    default String description() {
        return "%s %.2f %s".formatted(kind(), amountCents() / 100.0, currency());
    }
}
