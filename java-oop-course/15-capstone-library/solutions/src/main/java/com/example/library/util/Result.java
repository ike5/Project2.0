package com.example.library.util;

public sealed interface Result<T, E> permits Result.Ok, Result.Err {
    record Ok<T, E>(T value)  implements Result<T, E> {}
    record Err<T, E>(E error) implements Result<T, E> {}

    static <T, E> Result<T, E> ok(T value)  { return new Ok<>(value); }
    static <T, E> Result<T, E> err(E error) { return new Err<>(error); }

    default boolean isOk()  { return this instanceof Ok; }
    default boolean isErr() { return this instanceof Err; }

    default T orElseThrow() {
        return switch (this) {
            case Ok<T, E> ok  -> ok.value();
            case Err<T, E> err -> { throw new IllegalStateException("Result is Err: " + err.error()); }
        };
    }

    default E error() {
        return switch (this) {
            case Ok<T, E> ok   -> throw new IllegalStateException("Result is Ok: " + ok.value());
            case Err<T, E> err -> err.error();
        };
    }
}
