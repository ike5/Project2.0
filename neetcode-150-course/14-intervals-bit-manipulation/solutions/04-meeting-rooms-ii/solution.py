"""Meeting Rooms II.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/04-meeting-rooms-ii/solution.py
"""



def min_meeting_rooms(intervals: list[list[int]]) -> int:
    starts = sorted(a for a, _ in intervals)
    ends = sorted(b for _, b in intervals)
    rooms = 0
    end_ptr = 0
    for s in starts:
        if s >= ends[end_ptr]:
            end_ptr += 1
        else:
            rooms += 1
    return rooms


def _self_test() -> None:
    assert min_meeting_rooms([[0, 30], [5, 10], [15, 20]]) == 2, f"test 1 failed: got { min_meeting_rooms([[0, 30], [5, 10], [15, 20]])!r } expected { 2!r }"
    assert min_meeting_rooms([[7, 10], [2, 4]]) == 1, f"test 2 failed: got { min_meeting_rooms([[7, 10], [2, 4]])!r } expected { 1!r }"
    print(f"all 2 tests passed for min_meeting_rooms")


if __name__ == "__main__":
    _self_test()
