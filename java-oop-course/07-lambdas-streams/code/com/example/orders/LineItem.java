package com.example.orders;

public record LineItem(String sku, int quantity, long unitPriceCents) {
    public long lineTotal() { return (long) quantity * unitPriceCents; }
}
