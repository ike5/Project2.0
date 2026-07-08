package com.example.collections;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        var entry = Pair.of("answer", 42);
        System.out.println(entry);

        var bag = new HashMap<String, Number>();
        Pair.putIfAbsent(bag, Pair.<String, Integer>of("answer", 42));
        Pair.putIfAbsent(bag, Pair.<String, Double>of("pi", 3.14));
        System.out.println(bag);

        System.out.println(Algorithms.max(List.of(3, 1, 4, 1, 5, 9, 2, 6)));

        var names = List.of("Ada", "Grace", "Alan");
        System.out.println(Algorithms.max(names, (a, b) -> Integer.compare(a.length(), b.length())));

        List<Integer> src = List.of(1, 2, 3);
        List<Number>  dst = new ArrayList<>();
        Copy.copy(src, dst);
        System.out.println(dst);

        List<String>  ss = new ArrayList<>();
        List<Integer> is = new ArrayList<>();
        System.out.println(ss.getClass() == is.getClass());
    }
}
