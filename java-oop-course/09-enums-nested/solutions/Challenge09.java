package com.example.workflow;

import java.util.Comparator;
import java.util.EnumMap;
import java.util.Iterator;
import java.util.Map;
import java.util.NoSuchElementException;

public final class Challenge09 {

    private Challenge09() {}

    public static void main(String[] args) {
        // 1. Priority comparator.
        var priorities = java.util.Arrays.asList(Priority.LOW, Priority.URGENT, Priority.MEDIUM, Priority.HIGH);
        priorities.sort(Priority.BY_RANK);
        System.out.println(priorities);

        // 2. WorkflowStep state machine.
        WorkflowStep s = WorkflowStep.DRAFT;
        s = s.submit();
        s = s.approve();
        s = s.publish();
        System.out.println("final: " + s);

        // 3. DoublyLinkedList reverse.
        var dl = new DoublyLinkedList<String>();
        for (String x : "a b c d".split(" ")) dl.add(x);
        System.out.println("before: " + dl);
        dl.reverse();
        System.out.println("after:  " + dl);

        // 4. EnumMap week.
        EnumMap<Day, Schedule> week = new EnumMap<>(Day.class);
        week.put(Day.MON, new Schedule("deep work"));
        week.put(Day.TUE, new Schedule("meetings"));
        week.put(Day.WED, new Schedule("deep work"));
        week.put(Day.THU, new Schedule("deep work"));
        week.put(Day.FRI, new Schedule("review"));
        week.put(Day.SAT, new Schedule("weekend"));
        week.put(Day.SUN, new Schedule("weekend"));
        for (Day d : Day.values()) {
            System.out.println(d + ": " + week.get(d));
        }
    }

    // 1. Priority.
    public enum Priority {
        LOW, MEDIUM, HIGH, URGENT;
        // Higher ordinal = higher priority.
        public static final Comparator<Priority> BY_RANK = Comparator.comparingInt(Priority::ordinal);
    }

    // 2. WorkflowStep state machine.
    public enum WorkflowStep {
        DRAFT {
            @Override public WorkflowStep submit()  { return IN_REVIEW; }
            @Override public WorkflowStep approve() { return this; }     // can't approve a draft
            @Override public WorkflowStep reject()  { return this; }     // can't reject a draft
            @Override public WorkflowStep publish() { return this; }     // can't publish a draft
        },
        IN_REVIEW {
            @Override public WorkflowStep submit()  { return this; }
            @Override public WorkflowStep approve() { return APPROVED; }
            @Override public WorkflowStep reject()  { return REJECTED; }
            @Override public WorkflowStep publish() { return this; }
        },
        APPROVED {
            @Override public WorkflowStep submit()  { return this; }
            @Override public WorkflowStep approve() { return this; }
            @Override public WorkflowStep reject()  { return REJECTED; }
            @Override public WorkflowStep publish() { return PUBLISHED; }
        },
        REJECTED {
            @Override public WorkflowStep submit()  { return this; }
            @Override public WorkflowStep approve() { return this; }
            @Override public WorkflowStep reject()  { return this; }
            @Override public WorkflowStep publish() { return this; }
        },
        PUBLISHED {
            @Override public WorkflowStep submit()  { return this; }
            @Override public WorkflowStep approve() { return this; }
            @Override public WorkflowStep reject()  { return this; }
            @Override public WorkflowStep publish() { return this; }
        };
        public abstract WorkflowStep submit();
        public abstract WorkflowStep approve();
        public abstract WorkflowStep reject();
        public abstract WorkflowStep publish();
    }

    // 3. DoublyLinkedList with static nested Node.
    public static final class DoublyLinkedList<E> implements Iterable<E> {
        private Node<E> head, tail;
        private int size;

        public void add(E e) {
            Node<E> n = new Node<>(e, tail, null);
            if (tail != null) tail.next = n;
            else head = n;
            tail = n;
            size++;
        }
        public int size() { return size; }
        public void reverse() {
            Node<E> cur = head;
            while (cur != null) {
                Node<E> tmp = cur.next;
                cur.next = cur.prev;
                cur.prev = tmp;
                cur = tmp;
            }
            Node<E> tmp = head;
            head = tail;
            tail = tmp;
        }
        @Override public Iterator<E> iterator() {
            return new Iterator<>() {
                Node<E> cur = head;
                @Override public boolean hasNext() { return cur != null; }
                @Override public E next() {
                    if (cur == null) throw new NoSuchElementException();
                    E v = cur.value; cur = cur.next; return v;
                }
            };
        }
        @Override public String toString() {
            StringBuilder sb = new StringBuilder("[");
            for (E e : this) sb.append(e).append(", ");
            return sb.length() > 1 ? sb.substring(0, sb.length() - 2) + "]" : "[]";
        }
        private static final class Node<E> {
            E value;
            Node<E> prev, next;
            Node(E v, Node<E> p, Node<E> n) { value = v; prev = p; next = n; }
        }
    }

    // 4. EnumMap of days to schedules.
    public enum Day { MON, TUE, WED, THU, FRI, SAT, SUN }
    public record Schedule(String activity) {}
}
