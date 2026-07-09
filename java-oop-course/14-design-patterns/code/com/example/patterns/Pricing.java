package com.example.patterns;

public final class Pricing {
    public static final PricingStrategy REGULAR = base -> base;
    public static final PricingStrategy PREMIUM = base -> Math.round(base * 0.85);
    public static final PricingStrategy VIP     = base -> Math.round(base * 0.50);

    private Pricing() {}
}
