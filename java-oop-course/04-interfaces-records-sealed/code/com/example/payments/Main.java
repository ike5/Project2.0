package com.example.payments;

import java.util.List;

public class Main {
    public static void main(String[] args) {
        List<Payment> ledger = List.of(
            new CardPayment(12_99, "USD", "4242"),
            new CashPayment(5_00, "USD"),
            new BankTransfer(200_00, "USD", "acct-1234"),
            new ZeroPayment("USD")
        );

        for (Payment p : ledger) {
            System.out.println(render(p));
        }
    }

    public static String render(Payment p) {
        return switch (p) {
            case CardPayment c    -> "card    $" + (c.amountCents() / 100.0);
            case CashPayment c    -> "cash    $" + (c.amountCents() / 100.0);
            case BankTransfer b   -> "xfer    $" + (b.amountCents() / 100.0) + " from " + b.from();
            case ZeroPayment z    -> "zero";
        };
    }
}
