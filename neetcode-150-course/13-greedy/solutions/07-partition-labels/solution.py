"""Partition Labels.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/07-partition-labels/solution.py
"""



def partition_labels(s: str) -> list[int]:
    last = {c: i for i, c in enumerate(s)}
    out: list[int] = []
    start = end = 0
    for i, c in enumerate(s):
        end = max(end, last[c])
        if i == end:
            out.append(end - start + 1)
            start = i + 1
    return out


def _self_test() -> None:
    assert partition_labels('ababcbacadefegdehijhklij') == [9, 7, 8], f"test 1 failed: got { partition_labels('ababcbacadefegdehijhklij')!r } expected { [9, 7, 8]!r }"
    assert partition_labels('eccbbbbdec') == [10], f"test 2 failed: got { partition_labels('eccbbbbdec')!r } expected { [10]!r }"
    print(f"all 2 tests passed for partition_labels")


if __name__ == "__main__":
    _self_test()
