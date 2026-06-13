# Practice — Self-Graded, Endlessly Repeatable Drills 🎯

A bank of **auto-graded** exercises, one notebook per module. The trick: **every drill draws
a fresh random problem each time you run it** — a new line to fit, new blobs to separate, a
new subset of clothing to classify — so you can practice the *same skill* over and over with
**different predictions to train for** until it's automatic.

> No answer keys to peek at mid-drill: a hidden grader checks **your** result and prints ✅/❌
> with a helpful message. Worked solutions live in [`solutions/`](./solutions/) for when
> you're truly stuck.

## How to use

```bash
cd ml-pytorch-course
pip install -r requirements.txt          # the course deps
pip install jupyter                       # if you don't already have a notebook UI
jupyter notebook practice/                # or open the folder in VS Code / JupyterLab
```

In each notebook:

1. Run the **imports** cell once.
2. For each exercise: run the **task** cell (draws a fresh random problem) → write your code
   in the **YOUR CODE** cell → run the **check** cell for instant feedback.
3. The starter code already runs end-to-end (it just fails the check). Improve it until you
   pass.
4. **Re-run the task cell** for new numbers and do it again. Aim to **pass 5 different draws
   in a row** before moving on — that's the rep that builds intuition.

No Jupyter? Every drill also works in a plain Python REPL — `import practice_utils as pu`,
call a task generator, train, and call `task.grade(...)`. See the docstrings in
[`practice_utils.py`](./practice_utils.py).

## The notebooks

| Notebook | Drills you repeat | Mirrors |
|----------|-------------------|---------|
| [`01_tensors_autograd.ipynb`](./01_tensors_autograd.ipynb) | shape surgery, autograd derivatives, standardization, by-hand GD | Module 01 |
| [`02_gradient_descent.ipynb`](./02_gradient_descent.ipynb) | minimize hidden quadratics (1-D/2-D), pick a stable lr, use `torch.optim` | Module 02 |
| [`03_linear_regression.ipynb`](./03_linear_regression.ipynb) | recover a **random hidden line / relationship** each run; multi-feature + scaling | Module 03 |
| [`04_classification.ipynb`](./04_classification.ipynb) | train MLPs on **fresh blobs & moons**; hit accuracy targets | Module 04 |
| [`05_cnns.ipynb`](./05_cnns.ipynb) | build & train a **CNN on a random FashionMNIST subset** | Module 05 |
| [`06_training_techniques.ipynb`](./06_training_techniques.ipynb) | beat overfitting on small-data draws (regularization + early stopping) | Module 06 |
| [`07_capstone.ipynb`](./07_capstone.ipynb) | squeeze max accuracy from a hard random subset | Module 07 |

## What "different predictions to train for" means

The task generators in `practice_utils.py` hide a fresh ground truth on every call:

- **Regression** — a new `y = w·x + b + noise` with random weights, scales, and noise. The
  pass bar sits just above the (hidden) noise floor, so you must actually fit the *signal*.
- **Classification** — a new number of classes and new cluster positions / moon rotation.
- **Images** — a new random subset of FashionMNIST classes (relabeled `0..k-1`).
- **Optimization** — a new hidden minimizer to descend to.

Because the grader owns the truth and only scores your output, you can't game it — you have
to genuinely train a model that generalizes to its held-out check set.

## Files

- [`practice_utils.py`](./practice_utils.py) — the `Grader` + all random task generators (the
  one file to read if you want to write your own drills).
- [`build_notebooks.py`](./build_notebooks.py) — regenerates every notebook from a single
  spec (`python build_notebooks.py`). Edit here to add/modify drills.
- [`solutions/`](./solutions/) — worked solution notebooks. Try the learner version first!

---

← Back to the [course](../README.md). These drills pair with the modules — read a module,
do its lab, then grind its practice notebook until passing is automatic.
