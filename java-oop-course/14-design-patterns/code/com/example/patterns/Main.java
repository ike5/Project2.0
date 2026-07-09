package com.example.patterns;

import java.util.List;

public class Main {
    public static void main(String[] args) {
        var order = Order.builder()
                .id(1).customer("Ada").baseCents(10_00)
                .build()
                .apply(Pricing.PREMIUM);
        System.out.println("order: " + order + " (final " + order.finalCents() + " cents)");

        Text text = Text.of("Hello, Java").bold().italic();
        System.out.println("text: " + text.render());

        var bus = new EventBus<String>();
        Runnable s1 = bus.subscribe(msg -> System.out.println("sub1: " + msg));
        Runnable s2 = bus.subscribe(msg -> System.out.println("sub2: " + msg));
        bus.publish("event 1");
        bus.publish("event 2");
        s1.run();   // unsubscribe s1
        s2.run();   // unsubscribe s2
        bus.publish("(no listeners)");

        List<Order> bulk = List.of(
                Order.builder().id(2).customer("Grace").baseCents(5_00).build(),
                Order.builder().id(3).customer("Alan").baseCents(20_00).build()
        );
        System.out.println("bulk: " + bulk);
    }
}
