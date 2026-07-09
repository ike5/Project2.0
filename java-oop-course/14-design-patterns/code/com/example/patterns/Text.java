package com.example.patterns;

@FunctionalInterface
public interface Text {
    String render();

    static Text of(String s) { return () -> s; }

    default Text bold()      { return () -> "<b>" + render() + "</b>"; }
    default Text italic()    { return () -> "<i>" + render() + "</i>"; }
    default Text underline() { return () -> "<u>" + render() + "</u>"; }
}
