package com.example.workflow;

public enum Direction {
    NORTH, EAST, SOUTH, WEST;

    public Direction left()      { return vals()[(ordinal() + 3) % 4]; }
    public Direction right()     { return vals()[(ordinal() + 1) % 4]; }
    public Direction opposite()  { return vals()[(ordinal() + 2) % 4]; }

    private static Direction[] vals() { return values(); }
}
