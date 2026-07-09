"""Car Fleet.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/06-car-fleet/solution.py
"""



def car_fleet(target: int, position: list[int], speed: list[int]) -> int:
    cars = sorted(zip(position, speed), reverse=True)
    fleets = 0
    cur_time = 0.0
    for p, s in cars:
        time = (target - p) / s
        if time > cur_time:
            fleets += 1
            cur_time = time
    return fleets


def _self_test() -> None:
    assert car_fleet(12, [10, 8, 0, 5, 3], [2, 4, 1, 1, 3]) == 3, f"test 1 failed: got { car_fleet(12, [10, 8, 0, 5, 3], [2, 4, 1, 1, 3])!r } expected { 3!r }"
    assert car_fleet(10, [3], [3]) == 1, f"test 2 failed: got { car_fleet(10, [3], [3])!r } expected { 1!r }"
    assert car_fleet(100, [0, 2, 4], [4, 2, 1]) == 1, f"test 3 failed: got { car_fleet(100, [0, 2, 4], [4, 2, 1])!r } expected { 1!r }"
    print(f"all 3 tests passed for car_fleet")


if __name__ == "__main__":
    _self_test()
