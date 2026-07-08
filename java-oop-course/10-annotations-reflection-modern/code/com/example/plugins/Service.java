package com.example.plugins;

public final class Service {
    @Timed
    public String fastOp() { return "fast"; }

    @Timed(unit = "ns")
    public String slowerOp() throws InterruptedException {
        Thread.sleep(5);
        return "slow";
    }

    public String unTimed() { return "untracked"; }
}
