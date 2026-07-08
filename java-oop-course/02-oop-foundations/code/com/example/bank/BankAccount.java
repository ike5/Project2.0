package com.example.bank;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Objects;

public final class BankAccount {

    private static long nextAccountNumber = 1_000L;

    private final long accountNumber;
    private final String owner;
    private long balanceCents;

    public BankAccount(String owner, long openingBalanceCents) {
        this.accountNumber = nextAccountNumber++;
        this.owner = Objects.requireNonNull(owner, "owner");
        if (openingBalanceCents < 0) {
            throw new IllegalArgumentException("opening balance must be >= 0");
        }
        this.balanceCents = openingBalanceCents;
    }

    public static BankAccount open(String owner) {
        return new BankAccount(owner, 0L);
    }

    public static BankAccount openWithDeposit(String owner, long cents) {
        return new BankAccount(owner, cents);
    }

    public long accountNumber() { return accountNumber; }
    public String owner()       { return owner; }
    public long balanceCents()  { return balanceCents; }

    public void deposit(long amountCents) {
        if (amountCents <= 0) throw new IllegalArgumentException("amount must be > 0");
        balanceCents += amountCents;
    }

    public void withdraw(long amountCents) {
        if (amountCents <= 0) throw new IllegalArgumentException("amount must be > 0");
        if (amountCents > balanceCents) {
            throw new IllegalStateException("insufficient funds");
        }
        balanceCents -= amountCents;
    }

    public void applyMonthlyInterest(BigDecimal rate) {
        Objects.requireNonNull(rate, "rate");
        if (rate.signum() < 0) {
            throw new IllegalArgumentException("rate must be >= 0");
        }
        BigDecimal interest = BigDecimal.valueOf(balanceCents)
                .multiply(rate)
                .setScale(0, RoundingMode.HALF_EVEN);
        balanceCents += interest.longValueExact();
    }

    @Override
    public String toString() {
        return "BankAccount[%d owner=%s balance=%.2f]"
                .formatted(accountNumber, owner, balanceCents / 100.0);
    }

    @Override
    public boolean equals(Object o) {
        return o instanceof BankAccount other && accountNumber == other.accountNumber;
    }

    @Override
    public int hashCode() {
        return Objects.hash(accountNumber);
    }
}
