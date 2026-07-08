package com.example.orders;

import java.time.Instant;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        var now = Instant.now();
        var orders = List.of(
            new Order(1, "Ada",    List.of("a", "b"),  1200, now.minusSeconds(60)),
            new Order(2, "Grace",  List.of("c"),       500,  now.minusSeconds(30)),
            new Order(3, "Ada",    List.of("d", "e"),  4500, now.minusSeconds(10)),
            new Order(4, "Alan",   List.of("f"),      20000, now.minusSeconds(120))
        );

        System.out.println("large (>=$10): " + Reporting.largeOrders(orders, 1000));
        System.out.println("revenue: " + Reporting.totalRevenue(orders));
        System.out.println("by customer: " + Reporting.revenueByCustomer(orders));
        System.out.println("most recent: " + Reporting.mostRecent(orders).orElseThrow());
        System.out.println("top 2: " + Reporting.topCustomersBySpend(orders, 2));
        System.out.println("recent (60s): " + Reporting.recentOrders(orders, 60).size());
    }
}
