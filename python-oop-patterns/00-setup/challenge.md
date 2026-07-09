# Challenge 00 — Setup check

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Run every check from `../VERIFY.md`.** Confirm Python version, venv active, pytest installed, smoke script runs, and the repo layout matches.
2. **Add one container to the tour.** Pick a container that *isn't* in `00-setup/code/containers_tour.py` (or use one of them) and add a tiny demo function. Run it.
3. **Write a `pytest` test that uses `pytest.approx`.** In `00-setup/code/test_my_first.py`, write a test that checks `0.1 + 0.2 == pytest.approx(0.3)`. Confirm it passes.

## Success criteria

- [ ] `python 00-setup/code/smoke_test.py` prints `OK: Python is ready for LeetCode.`
- [ ] `python -m pytest 00-setup/code/test_smoke.py` passes.
- [ ] `python -m pytest 00-setup/code/test_my_first.py` passes.
- [ ] You can explain (in one sentence each) the difference between `list`, `dict`, `set`, and `tuple`.
