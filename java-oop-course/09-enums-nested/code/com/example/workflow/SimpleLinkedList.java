package com.example.workflow;

import java.util.Iterator;
import java.util.NoSuchElementException;

public final class SimpleLinkedList<E> implements Iterable<E> {
    private Node<E> head;
    private int size;

    public void add(E e) {
        Node<E> n = new Node<>(e, null);
        if (head == null) { head = n; }
        else {
            Node<E> cur = head;
            while (cur.next != null) cur = cur.next;
            cur.next = n;
        }
        size++;
    }
    public int size() { return size; }

    @Override
    public Iterator<E> iterator() {
        return new Iterator<>() {
            Node<E> cur = head;
            @Override public boolean hasNext() { return cur != null; }
            @Override public E next() {
                if (cur == null) throw new NoSuchElementException();
                E v = cur.value;
                cur = cur.next;
                return v;
            }
        };
    }

    private static final class Node<E> {
        E value;
        Node<E> next;
        Node(E v, Node<E> n) { value = v; next = n; }
    }
}
