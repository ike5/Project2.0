package com.example.workflow;

import java.util.EnumSet;

public class Main {
    public static void main(String[] args) {
        for (Operation op : Operation.values()) {
            System.out.println("3 " + op.symbol() + " 4 = " + op.apply(3, 4));
        }

        Direction d = Direction.NORTH;
        System.out.println(d + " -> left = " + d.left() + " | right = " + d.right() + " | opposite = " + d.opposite());

        EnumSet<Day> weekend = EnumSet.of(Day.SAT, Day.SUN);
        System.out.println("weekend size: " + weekend.size());

        var list = new SimpleLinkedList<String>();
        for (String s : "the quick brown fox".split(" ")) list.add(s);
        for (String s : list) System.out.println(s);
    }

    enum Day { MON, TUE, WED, THU, FRI, SAT, SUN }
}
