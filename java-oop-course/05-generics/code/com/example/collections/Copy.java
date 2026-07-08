package com.example.collections;

import java.util.List;

public final class Copy {
    private Copy() {}

    public static <T> void copy(List<? extends T> src, List<? super T> dst) {
        for (T t : src) dst.add(t);
    }
}
