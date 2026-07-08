package com.example.registry;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Deque;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;

public class Main {
    public static void main(String[] args) {
        Index<String, String> byAuthor = new Index<>();
        byAuthor.add("Ada", "On the Analytical Engine");
        byAuthor.add("Ada", "Notes on the Bernoulli Numbers");
        byAuthor.add("Grace", "On a New Programming Language");
        byAuthor.add("Grace", "The Linker");

        byAuthor.keys().forEach(k ->
                System.out.println(k + " -> " + byAuthor.get(k)));

        Deque<Integer> stack = new ArrayDeque<>();
        for (int x : List.of(1, 2, 3)) stack.push(x);
        while (!stack.isEmpty()) System.out.print(stack.pop() + " ");
        System.out.println();

        PriorityQueue<Integer> pq = new PriorityQueue<>();
        for (int x : List.of(5, 1, 3, 2, 4)) pq.offer(x);
        while (!pq.isEmpty()) System.out.print(pq.poll() + " ");
        System.out.println();

        record Person(String name, int age) {}
        var people = new ArrayList<Person>(List.of(
                new Person("Ada", 36),
                new Person("Grace", 85),
                new Person("Alan", 41)));
        people.sort(Comparator.comparingInt(Person::age).thenComparing(Person::name));
        people.forEach(System.out::println);

        // Map.merge as a counter.
        String text = "the quick brown fox jumps over the lazy dog";
        Map<String, Long> counts = new HashMap<>();
        for (String w : text.split(" ")) {
            counts.merge(w, 1L, Long::sum);
        }
        counts.forEach((k, v) -> System.out.println(k + " = " + v));
    }
}
