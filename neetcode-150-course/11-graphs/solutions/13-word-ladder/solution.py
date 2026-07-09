"""Word Ladder.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/13-word-ladder/solution.py
"""



def ladder_length(begin_word: str, end_word: str, word_list: list[str]) -> int:
    word_set = set(word_list)
    if end_word not in word_set:
        return 0
    from collections import deque
    q: deque[tuple[str, int]] = deque([(begin_word, 1)])
    visited = {begin_word}
    L = len(begin_word)
    while q:
        word, d = q.popleft()
        if word == end_word:
            return d
        for i in range(L):
            for c in 'abcdefghijklmnopqrstuvwxyz':
                if c == word[i]:
                    continue
                nw = word[:i] + c + word[i + 1:]
                if nw in word_set and nw not in visited:
                    visited.add(nw)
                    q.append((nw, d + 1))
    return 0


def _self_test() -> None:
    assert ladder_length('hit', 'cog', ['hot', 'dot', 'dog', 'lot', 'log', 'cog']) == 5, f"test 1 failed: got { ladder_length('hit', 'cog', ['hot', 'dot', 'dog', 'lot', 'log', 'cog'])!r } expected { 5!r }"
    assert ladder_length('hit', 'cog', ['hot', 'dot', 'dog', 'lot', 'log']) == 0, f"test 2 failed: got { ladder_length('hit', 'cog', ['hot', 'dot', 'dog', 'lot', 'log'])!r } expected { 0!r }"
    print(f"all 2 tests passed for ladder_length")


if __name__ == "__main__":
    _self_test()
