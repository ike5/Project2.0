package com.example.patterns;

@FunctionalInterface
public interface PricingStrategy {
    long price(long baseCents);
}
