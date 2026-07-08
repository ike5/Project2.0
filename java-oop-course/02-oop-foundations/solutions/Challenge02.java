package com.example.bank;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Currency;
import java.util.List;
import java.util.Objects;

public final class Challenge02 {

    private Challenge02() {}

    public static void main(String[] args) {
        // 1. Money add/subtract/multiply.
        Money m1 = Money.usd(10_00);
        Money m2 = Money.usd(2_50);
        System.out.println(m1.add(m2));         // 12.50 USD
        System.out.println(m1.subtract(m2));    // 7.50 USD
        System.out.println(m1.multiply(3));      // 30.00 USD

        try { m1.add(new Money(1, Currency.getInstance("EUR"))); }
        catch (IllegalArgumentException e) { System.out.println("rejected: " + e.getMessage()); }

        try { Money.usd(-1); }
        catch (IllegalArgumentException e) { System.out.println("rejected: " + e.getMessage()); }

        // 2. Negative-rate rejection.
        var acct = BankAccount.open("Ada");
        try { acct.applyMonthlyInterest(new BigDecimal("-0.05")); }
        catch (IllegalArgumentException e) { System.out.println("rejected: " + e.getMessage()); }
        acct.applyMonthlyInterest(new BigDecimal("0.01"));
        System.out.println(acct);  // balance grew by 1%

        // 3. Color equality + Set.
        var red1 = new Color(255, 0, 0);
        var red2 = new Color(255, 0, 0);
        var blue = new Color(0, 0, 255);
        var set = new java.util.HashSet<Color>();
        set.add(red1); set.add(red2); set.add(blue);
        System.out.println("set size: " + set.size());  // 2 (red deduped)
        System.out.println("red1 == red2: " + red1.equals(red2));

        // 4. Defensive copies.
        var input = new ArrayList<String>(List.of("Ada", "Grace"));
        var team  = new Team(input);
        input.add("Mallory");
        System.out.println("team still: " + team.members());   // doesn't include Mallory

        try { team.members().add("evil"); }
        catch (UnsupportedOperationException e) { System.out.println("rejected: mutation"); }
    }

    // -------- 1. Money (class form) --------
    public static final class Money {
        private final long cents;
        private final Currency currency;

        public Money(long cents, Currency currency) {
            if (cents < 0) throw new IllegalArgumentException("cents must be >= 0");
            this.currency = Objects.requireNonNull(currency, "currency");
            this.cents = cents;
        }

        public static Money usd(long cents) {
            return new Money(cents, Currency.getInstance("USD"));
        }

        public long cents()        { return cents; }
        public Currency currency() { return currency; }

        public Money add(Money other) {
            requireSameCurrency(other);
            return new Money(cents + other.cents, currency);
        }
        public Money subtract(Money other) {
            requireSameCurrency(other);
            if (other.cents > cents) throw new IllegalArgumentException("insufficient");
            return new Money(cents - other.cents, currency);
        }
        public Money multiply(int n) {
            if (n < 0) throw new IllegalArgumentException("n must be >= 0");
            return new Money(cents * n, currency);
        }
        private void requireSameCurrency(Money other) {
            if (!currency.equals(other.currency)) {
                throw new IllegalArgumentException("currency mismatch");
            }
        }
        @Override public String toString() {
            return "%.2f %s".formatted(cents / 100.0, currency.getCurrencyCode());
        }
        @Override public boolean equals(Object o) {
            return o instanceof Money m && cents == m.cents && currency.equals(m.currency);
        }
        @Override public int hashCode() { return Objects.hash(cents, currency); }
    }

    // -------- 3. Color --------
    public static final class Color {
        private final int r, g, b;
        public Color(int r, int g, int b) {
            if (r < 0 || r > 255 || g < 0 || g > 255 || b < 0 || b > 255) {
                throw new IllegalArgumentException("rgb out of range");
            }
            this.r = r; this.g = g; this.b = b;
        }
        public int red()   { return r; }
        public int green() { return g; }
        public int blue()  { return b; }
        @Override public String toString() { return "Color(%d,%d,%d)".formatted(r, g, b); }
        @Override public boolean equals(Object o) {
            return o instanceof Color c && r == c.r && g == c.g && b == c.b;
        }
        @Override public int hashCode() { return Objects.hash(r, g, b); }
    }

    // -------- 4. Team (defensive copy) --------
    public static final class Team {
        private final List<String> members;
        public Team(List<String> members) {
            this.members = new ArrayList<>(members);    // copy IN
        }
        public List<String> members() {
            return java.util.Collections.unmodifiableList(members);   // copy OUT (read-only view)
        }
    }
}
