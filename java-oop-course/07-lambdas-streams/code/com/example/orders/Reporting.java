package com.example.orders;

import java.time.Instant;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

public final class Reporting {
    private Reporting() {}

    public static List<Order> largeOrders(List<Order> orders, long thresholdCents) {
        return orders.stream()
                .filter(o -> o.totalCents() >= thresholdCents)
                .sorted(Comparator.comparing(Order::totalCents).reversed())
                .toList();
    }

    public static long totalRevenue(List<Order> orders) {
        return orders.stream().mapToLong(Order::totalCents).sum();
    }

    public static Map<String, Long> revenueByCustomer(List<Order> orders) {
        return orders.stream().collect(Collectors.groupingBy(
                Order::customer,
                Collectors.summingLong(Order::totalCents)));
    }

    public static Optional<Order> mostRecent(List<Order> orders) {
        return orders.stream().max(Comparator.comparing(Order::placedAt));
    }

    public static List<Map.Entry<String, Long>> topCustomersBySpend(List<Order> orders, int n) {
        return revenueByCustomer(orders).entrySet().stream()
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
                .limit(n)
                .toList();
    }

    public static List<Order> recentOrders(List<Order> orders, long seconds) {
        Instant cutoff = Instant.now().minusSeconds(seconds);
        return orders.stream()
                .filter(o -> o.placedAt().isAfter(cutoff))
                .toList();
    }
}
