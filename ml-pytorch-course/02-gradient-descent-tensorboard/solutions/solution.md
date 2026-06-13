# Solution 02 — notes

Run: `python 02-gradient-descent-tensorboard/solutions/challenge_solution.py`
then `tensorboard --logdir runs`.

## Key points

- **Curved valleys are hard.** The Rosenbrock-ish loss has a banana-shaped valley; the
  gradient mostly points *across* it, not *along* it, so plain SGD inches along the floor.
  This is the classic motivation for momentum/Adam.

- **Learning rate (Task 2).** This surface is far more sensitive than Module 02's bowl. A
  too-large lr makes the `10*(w2 - w1²)²` term explode (the path flings outward). The
  "good" lr is small and steady; the curve goes down monotonically.

- **Gradient-norm story (Task 3).** `grad/norm` starts large (steep outer walls of the
  valley), drops sharply as the optimizer falls into the trough, then decays slowly as it
  crawls toward `(1, 1)`. A `grad/norm` that's small but loss still high = you're in the
  flat valley floor, far from the minimum — exactly where momentum helps.

- **Optimizer showdown (Task 4).** Expect roughly: plain SGD needs the most steps (often
  doesn't reach `loss < 0.1` in 400 with a safe lr); momentum is much faster; Adam adapts
  its per-parameter step and typically reaches the threshold quickest. Numbers vary with
  lr — the point is the *ordering* and *why*.

- **Hand-update == `optim.SGD` (Task 5).** `torch.optim.SGD` with no momentum/weight-decay
  literally performs `p -= lr * p.grad`. The two trajectories match to floating-point
  tolerance, which demystifies what an "optimizer" is: a tidy container for the update rule
  you already wrote by hand in Module 01.

## Reading TensorBoard for this challenge

- **SCALARS:** overlay `loss` across the `chal02_lr_*` runs for the lr story; look at
  `grad/norm` for the steepness story.
- **IMAGES → descent/path:** scrub the slider on `chal02_lr_good` and the optimizer runs to
  watch the trajectory thread the curved valley.
