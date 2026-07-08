package com.example.workflow;

public enum Operation {
    ADD("+")      { public long apply(long a, long b) { return a + b; } },
    SUBTRACT("-") { public long apply(long a, long b) { return a - b; } },
    MULTIPLY("*") { public long apply(long a, long b) { return a * b; } },
    DIVIDE("/")   { public long apply(long a, long b) { return a / b; } };

    private final String symbol;
    Operation(String symbol) { this.symbol = symbol; }
    public String symbol() { return symbol; }
    public abstract long apply(long a, long b);
}
