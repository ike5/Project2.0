"""Generate the practice notebooks (learner + solution versions) from one spec.

Run from the practice/ directory:
    python build_notebooks.py

Produces:
    practice/NN_*.ipynb            (learner version: stubs + hints + auto-grader)
    practice/solutions/NN_*.ipynb  (worked solution version)

Each exercise = a randomized, self-graded drill. Re-run a task cell for a fresh problem.
This script is the single source of truth; edit it and re-run to regenerate the notebooks.
"""

import os

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

HERE = os.path.dirname(os.path.abspath(__file__))

COMMON_IMPORTS = """\
# Run me first. Imports + the practice toolkit (the grader and random task generators).
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')) if os.path.basename(os.getcwd()) != 'practice' else '.')
sys.path.insert(0, '.')
import torch
import torch.nn as nn
import practice_utils as pu
print('ready — torch', torch.__version__)\
"""

HOWTO = """\
**How these drills work**

1. Run the **imports** cell once.
2. For each exercise: run the **task** cell to draw a *fresh random problem*, write your
   solution in the **YOUR CODE** cell, then run the **check** cell for instant ✅/❌ feedback.
3. The starter code already runs end-to-end (it just fails the check). Improve it until the
   check passes.
4. **Re-run the task cell** to get new numbers/targets and do it again. Aim to pass 5
   different draws in a row before moving on — that's how it sticks.

> The grader holds a hidden ground truth and checks *your* result; it never reveals the
> answer. Stuck? See the matching notebook in `solutions/`.\
"""


def exercise(title, prompt, task_code, stub_code, solution_code, check_code):
    """Return (learner_cells, solution_cells) for one exercise."""
    head = new_markdown_cell(f"## {title}\n\n{prompt}")
    task = new_code_cell(task_code)
    learner_code = new_code_cell("# ✏️ YOUR CODE — edit this cell\n" + stub_code)
    sol_code = new_code_cell("# ✅ reference solution\n" + solution_code)
    check = new_code_cell("# check (run after your code)\n" + check_code)
    return ([head, task, learner_code, check], [head, task, sol_code, check])


def build(filename, title, intro, exercises, outro=None):
    learner = [new_markdown_cell(f"# {title}\n\n{intro}\n\n---\n\n{HOWTO}"),
               new_code_cell(COMMON_IMPORTS)]
    solution = [new_markdown_cell(f"# {title} — SOLUTIONS\n\n"
                                  "Worked answers. Try the learner notebook first!"),
                new_code_cell(COMMON_IMPORTS)]
    for ex in exercises:
        lc, sc = ex
        learner += lc
        solution += sc
    if outro:
        learner.append(new_markdown_cell(outro))
        solution.append(new_markdown_cell(outro))

    nb_l = new_notebook(cells=learner, metadata=_meta())
    nb_s = new_notebook(cells=solution, metadata=_meta())
    nbformat.write(nb_l, os.path.join(HERE, filename))
    os.makedirs(os.path.join(HERE, "solutions"), exist_ok=True)
    nbformat.write(nb_s, os.path.join(HERE, "solutions", filename))
    print("wrote", filename, "and solutions/" + filename)


def _meta():
    return {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"}}


# ======================================================================================
# Notebook 01 — Tensors & Autograd
# ======================================================================================
nb01 = [
    exercise(
        "Drill 1 — Shape surgery",
        "Reshape the source tensor into the **target shape** the task gives you. "
        "Use `reshape`/`view`/`permute`/`unsqueeze`. Re-run the task cell for a new target.",
        "src, target = pu.random_shape_target()\nprint('source shape', tuple(src.shape), '-> reshape to', target)",
        "out = src                      # TODO: reshape `src` into `target`",
        "out = src.reshape(*target)",
        "g = pu.Grader('shape surgery'); g.shape(out, target, 'out shape'); g.summary()",
    ),
    exercise(
        "Drill 2 — Derivative with autograd",
        "The task gives polynomial coefficients `[c0,c1,c2,c3]` (so "
        "`f(x)=c0+c1·x+c2·x²+c3·x³`) and a point `x0`. Use **autograd** to compute `df/dx` at "
        "`x0` into `student_grad`.",
        "coeffs, x0 = pu.random_poly()\nprint('coeffs', coeffs, ' x0', x0)",
        "student_grad = 0.0             # TODO: build x with requires_grad, f, backward(), read x.grad",
        "x = torch.tensor(x0, requires_grad=True)\n"
        "f = coeffs[0] + coeffs[1]*x + coeffs[2]*x**2 + coeffs[3]*x**3\n"
        "f.backward()\nstudent_grad = x.grad.item()",
        "pu.grade_derivative(coeffs, x0, student_grad)",
    ),
    exercise(
        "Drill 3 — Standardize the columns",
        "Standardize matrix `X` so every **column** has mean ≈ 0 and std ≈ 1, into `Z` "
        "(use `dim=0, keepdim=True` and broadcasting).",
        "X = torch.randn(200, 4) * torch.tensor([5., 0.1, 20., 1.]) + torch.tensor([3., -1., 50., 0.])\n"
        "print('raw col means', [round(v,2) for v in X.mean(0).tolist()])",
        "Z = X                          # TODO: subtract per-column mean, divide by per-column std",
        "Z = (X - X.mean(0, keepdim=True)) / X.std(0, keepdim=True)",
        "g = pu.Grader('standardize')\n"
        "g.at_most(Z.mean(0).abs().max().item(), 1e-4, 'max |col mean|')\n"
        "g.almost(Z.std(0).mean().item(), 1.0, 1e-2, 'avg col std'); g.summary()",
    ),
    exercise(
        "Drill 4 — Gradient of a vector loss",
        "For `loss = (w**2).sum()` the gradient is `2*w`. Fill `w.grad` via autograd into "
        "`student_grad` and match it.",
        "w = torch.randn(5, requires_grad=True)\nprint('w', [round(v,3) for v in w.tolist()])",
        "student_grad = torch.zeros_like(w)   # TODO: loss = (w**2).sum(); loss.backward(); read w.grad",
        "loss = (w**2).sum()\nloss.backward()\nstudent_grad = w.grad",
        "g = pu.Grader('vector grad')\n"
        "g.at_most((student_grad - 2*w).abs().max().item(), 1e-5, 'max error vs 2*w'); g.summary()",
    ),
    exercise(
        "Drill 5 — Minimize a random quadratic (by hand)",
        "Minimize a quadratic with a **hidden** minimizer using gradient descent you write "
        "yourself (autograd for the gradient, `w -= lr*w.grad` under `no_grad`). Reach the min "
        "into `w_final`.",
        "task = pu.quadratic_task(dim=1)\ntask.describe()",
        "w_final = task.start.clone()   # TODO: run gradient descent on task.loss(w) to the minimizer",
        "w = task.start.clone().requires_grad_(True)\n"
        "for _ in range(500):\n"
        "    loss = task.loss(w)\n    loss.backward()\n"
        "    with torch.no_grad():\n        w -= 0.1 * w.grad\n    w.grad.zero_()\n"
        "w_final = w.detach()",
        "task.grade(w_final)",
    ),
]

# ======================================================================================
# Notebook 02 — Gradient Descent
# ======================================================================================
nb02 = [
    exercise(
        "Drill 1 — Hand-rolled GD in 1-D",
        "Minimize a hidden 1-D quadratic with your own gradient-descent loop. Tune the "
        "learning rate / steps so `w_final` reaches the minimizer.",
        "task = pu.quadratic_task(dim=1)\ntask.describe()",
        "w_final = task.start.clone()   # TODO: GD loop using task.loss(w) and autograd",
        "w = task.start.clone().requires_grad_(True)\n"
        "for _ in range(800):\n    task.loss(w).backward()\n"
        "    with torch.no_grad():\n        w -= 0.08 * w.grad\n    w.grad.zero_()\n"
        "w_final = w.detach()",
        "task.grade(w_final)",
    ),
    exercise(
        "Drill 2 — GD in 2-D",
        "Same idea, two parameters. The minimizer is a hidden 2-vector; descend to it.",
        "task = pu.quadratic_task(dim=2)\ntask.describe()",
        "w_final = task.start.clone()   # TODO: 2-D gradient descent",
        "w = task.start.clone().requires_grad_(True)\n"
        "for _ in range(1500):\n    task.loss(w).backward()\n"
        "    with torch.no_grad():\n        w -= 0.05 * w.grad\n    w.grad.zero_()\n"
        "w_final = w.detach()",
        "task.grade(w_final)",
    ),
    exercise(
        "Drill 3 — Let torch.optim do the stepping",
        "Re-solve the quadratic, but use a **real optimizer** (`torch.optim.SGD` or `Adam`) "
        "instead of hand-updating. Same `zero_grad → backward → step` ritual.",
        "task = pu.quadratic_task(dim=2)\ntask.describe()",
        "w = task.start.clone().requires_grad_(True)\nw_final = w.detach().clone()   # TODO: optimize w with torch.optim",
        "w = task.start.clone().requires_grad_(True)\n"
        "opt = torch.optim.Adam([w], lr=0.1)\n"
        "for _ in range(1000):\n    opt.zero_grad()\n    task.loss(w).backward()\n    opt.step()\n"
        "w_final = w.detach()",
        "task.grade(w_final)",
    ),
    exercise(
        "Drill 4 — Pick a learning rate that converges",
        "A quadratic's curvature is hidden. If your lr is too big you'll diverge; too small "
        "and 200 steps won't reach the minimum. Find an lr that lands `w_final` on the "
        "minimizer in **just 200 steps**.",
        "task = pu.quadratic_task(dim=1)\ntask.describe()",
        "lr = 0.001                     # TODO: tune this\n"
        "w = task.start.clone().requires_grad_(True)\n"
        "for _ in range(200):\n    task.loss(w).backward()\n"
        "    with torch.no_grad():\n        w -= lr * w.grad\n    w.grad.zero_()\n"
        "w_final = w.detach()",
        "lr = 0.2\n"
        "w = task.start.clone().requires_grad_(True)\n"
        "for _ in range(200):\n    task.loss(w).backward()\n"
        "    with torch.no_grad():\n        w -= lr * w.grad\n    w.grad.zero_()\n"
        "w_final = w.detach()",
        "task.grade(w_final)",
    ),
]

# ======================================================================================
# Notebook 03 — Linear Regression (train for different relationships)
# ======================================================================================
nb03 = [
    exercise(
        "Drill 1 — Recover a random line",
        "The task hides a relationship `y = w·x + b + noise` with **fresh `w`, `b`, and noise "
        "each draw**. Train a model on `train_data()` so it predicts the hidden test set well.",
        "task = pu.regression_task(n_features=1)\ntask.describe()\nXtr, ytr = task.train_data()",
        "model = nn.Linear(1, 1)        # TODO: train this on (Xtr, ytr)",
        "model = nn.Linear(1, 1)\nopt = torch.optim.Adam(model.parameters(), lr=0.1)\nlf = nn.MSELoss()\n"
        "for _ in range(400):\n    opt.zero_grad()\n    lf(model(Xtr), ytr).backward()\n    opt.step()",
        "task.grade(model)",
    ),
    exercise(
        "Drill 2 — Multi-feature regression (mind the scales!)",
        "Now 3 input features on **different scales**. A raw fit struggles; **standardize the "
        "features** (and ideally the target), train, and wrap so the model maps raw `x → y`.",
        "task = pu.regression_task(n_features=3)\ntask.describe()\nXtr, ytr = task.train_data()",
        "model = nn.Linear(3, 1)        # TODO: standardize, train, and make model map RAW x -> y",
        "mx, sx = Xtr.mean(0, keepdim=True), Xtr.std(0, keepdim=True)\n"
        "my, sy = ytr.mean(), ytr.std()\nXs, ys = (Xtr - mx) / sx, (ytr - my) / sy\n"
        "lin = nn.Linear(3, 1)\nopt = torch.optim.Adam(lin.parameters(), lr=0.05)\nlf = nn.MSELoss()\n"
        "for _ in range(400):\n    opt.zero_grad()\n    lf(lin(Xs), ys).backward()\n    opt.step()\n"
        "class Wrapped(nn.Module):\n"
        "    def forward(self, X):\n        return lin((X - mx) / sx) * sy + my\n"
        "model = Wrapped()",
        "task.grade(model)",
    ),
    exercise(
        "Drill 3 — Beat a tighter target",
        "Same kind of task, but the bar sits close to the noise floor (you must actually fit "
        "the signal, not just predict the mean). Standardize, train longer / tune the lr.",
        "task = pu.regression_task(n_features=2, noise_mult=1.2)\ntask.describe()\nXtr, ytr = task.train_data()",
        "model = nn.Linear(2, 1)        # TODO: standardize + train well enough to pass 0.6 RMSE",
        "mx, sx = Xtr.mean(0, keepdim=True), Xtr.std(0, keepdim=True)\n"
        "my, sy = ytr.mean(), ytr.std()\nXs, ys = (Xtr - mx) / sx, (ytr - my) / sy\n"
        "lin = nn.Linear(2, 1)\nopt = torch.optim.Adam(lin.parameters(), lr=0.05)\nlf = nn.MSELoss()\n"
        "for _ in range(600):\n    opt.zero_grad()\n    lf(lin(Xs), ys).backward()\n    opt.step()\n"
        "class Wrapped(nn.Module):\n    def forward(self, X):\n        return lin((X - mx) / sx) * sy + my\n"
        "model = Wrapped()",
        "task.grade(model)",
    ),
]

# ======================================================================================
# Notebook 04 — Classification
# ======================================================================================
MLP_SOL = (
    "Xtr, ytr = task.train_data()\nn_out = int(ytr.max().item()) + 1\n"
    "mx, sx = Xtr.mean(0, keepdim=True), Xtr.std(0, keepdim=True)\n"
    "net = nn.Sequential(nn.Linear(2,32), nn.ReLU(), nn.Linear(32,32), nn.ReLU(), nn.Linear(32,n_out))\n"
    "opt = torch.optim.Adam(net.parameters(), lr=0.02)\nlf = nn.CrossEntropyLoss()\nXs = (Xtr - mx) / sx\n"
    "for _ in range(300):\n    opt.zero_grad()\n    lf(net(Xs), ytr).backward()\n    opt.step()\n"
    "class Wrapped(nn.Module):\n    def forward(self, X):\n        return net((X - mx) / sx)\n"
    "model = Wrapped()"
)
nb04 = [
    exercise(
        "Drill 1 — Classify random blobs",
        "The task makes **2–4 Gaussian clusters** at fresh positions each draw. Build an MLP "
        "whose output is logits `(N, n_classes)` and train it to ≥ 90% on the hidden test set. "
        "Remember: final layer width = number of classes; use `CrossEntropyLoss`.",
        "task = pu.classification_task()\ntask.describe()",
        "model = nn.Sequential(nn.Linear(2, 8), nn.ReLU(), nn.Linear(8, 4))  # TODO: set output size & TRAIN it",
        MLP_SOL,
        "task.grade(model)",
    ),
    exercise(
        "Drill 2 — The two-moons (needs nonlinearity)",
        "Two interleaving moons with random noise/rotation — **not** linearly separable. Train "
        "an MLP with ReLU activations to ≥ 90%. (A single `nn.Linear` will fail; that's the "
        "point.)",
        "task = pu.moons_task()\ntask.describe()",
        "model = nn.Sequential(nn.Linear(2, 2))            # TODO: add hidden layers + ReLU, then TRAIN",
        MLP_SOL,
        "task.grade(model)",
    ),
    exercise(
        "Drill 3 — Hit a tighter 95%",
        "Same blobs, but you must reach **95%**. Train longer / widen the net / tune the lr.",
        "task = pu.classification_task(threshold=0.95)\ntask.describe()",
        "model = nn.Sequential(nn.Linear(2, 8), nn.ReLU(), nn.Linear(8, 4))  # TODO: output size & TRAIN to 0.95",
        MLP_SOL,
        "task.grade(model)",
    ),
]

# ======================================================================================
# Notebook 05 — CNNs on images (random class subsets)
# ======================================================================================
CNN_SOL = (
    "train_loader, test_loader = task.loaders()\nk = task.n_classes\n"
    "model = nn.Sequential(\n"
    "    nn.Conv2d(1,32,3,padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),\n"
    "    nn.Conv2d(32,64,3,padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),\n"
    "    nn.Flatten(), nn.Linear(64*7*7,64), nn.ReLU(), nn.Linear(64,k))\n"
    "opt = torch.optim.Adam(model.parameters(), lr=1e-3)\nlf = nn.CrossEntropyLoss()\n"
    "for epoch in range(8):\n    model.train()\n"
    "    for xb, yb in train_loader:\n        opt.zero_grad()\n        lf(model(xb), yb).backward()\n        opt.step()\n"
    "    print('epoch', epoch+1, 'done')"
)
nb05 = [
    exercise(
        "Drill 1 — Classify a random clothing subset",
        "The task picks **3–5 random FashionMNIST classes** (relabeled `0..k-1`) and gives you "
        "train/test loaders. Build a small **CNN** (`Conv → ReLU → Pool` blocks → `Flatten` → "
        "`Linear`) with `k` outputs and train it to ≥ 90% test accuracy. Inputs are "
        "`(N,1,28,28)`; after two `MaxPool2d(2)` the map is `7×7`.\n\n"
        "*(First run downloads FashionMNIST to `./data`. A few epochs on CPU is enough.)*",
        "task = pu.fashion_subset_task()\ntask.describe()",
        "train_loader, test_loader = task.loaders()\n"
        "model = nn.Sequential(nn.Flatten(), nn.Linear(28*28, task.n_classes))  # TODO: make it a CNN and TRAIN it",
        CNN_SOL,
        "task.grade(model)   # device='cpu' by default",
    ),
    exercise(
        "Drill 2 — A harder draw, more classes",
        "Force **5 classes** (often includes look-alike tops). Train enough epochs / a strong "
        "enough CNN to still clear 90%.",
        "task = pu.fashion_subset_task(k=5, threshold=0.82)\ntask.describe()",
        "train_loader, test_loader = task.loaders()\n"
        "model = nn.Sequential(nn.Flatten(), nn.Linear(28*28, task.n_classes))  # TODO: CNN + train (try BatchNorm, more epochs)",
        CNN_SOL,
        "task.grade(model)",
    ),
]

# ======================================================================================
# Notebook 06 — Training techniques (generalization under pressure)
# ======================================================================================
REG_SOL = (
    "train_loader, test_loader = task.loaders()\nk = task.n_classes\n"
    "model = nn.Sequential(\n"
    "    nn.Conv2d(1,16,3,padding=1), nn.BatchNorm2d(16), nn.ReLU(), nn.MaxPool2d(2),\n"
    "    nn.Conv2d(16,32,3,padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),\n"
    "    nn.Flatten(), nn.Dropout(0.3), nn.Linear(32*7*7,64), nn.ReLU(), nn.Linear(64,k))\n"
    "opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)\nlf = nn.CrossEntropyLoss()\n"
    "import copy\nbest_acc, best_state, bad = 0.0, None, 0\n"
    "for epoch in range(15):\n    model.train()\n"
    "    for xb, yb in train_loader:\n        opt.zero_grad()\n        lf(model(xb), yb).backward()\n        opt.step()\n"
    "    model.eval()\n    correct = total = 0\n    import torch as _t\n"
    "    with _t.no_grad():\n"
    "        for xb, yb in test_loader:\n            correct += (model(xb).argmax(1)==yb).sum().item(); total += yb.size(0)\n"
    "    acc = correct/total\n    print('epoch', epoch+1, 'val acc', round(acc,4))\n"
    "    if acc > best_acc:\n        best_acc, best_state, bad = acc, copy.deepcopy(model.state_dict()), 0\n"
    "    else:\n        bad += 1\n        if bad >= 5:\n            print('early stop'); break\n"
    "model.load_state_dict(best_state)   # restore BEST (not last) weights"
)
nb06 = [
    exercise(
        "Drill 1 — Generalize from little data",
        "Only **150 images per class** — easy to overfit. Use **regularization** (BatchNorm, "
        "dropout, weight decay) and **early stopping** to reach the hidden-test target. Train a "
        "plain model first and watch it fall short, then add regularization.",
        "task = pu.fashion_subset_task(k=4, train_per_class=150, threshold=0.78)\ntask.describe()",
        "train_loader, test_loader = task.loaders()\n"
        "model = nn.Sequential(nn.Flatten(), nn.Linear(28*28, task.n_classes))  # TODO: regularized CNN + early stopping",
        REG_SOL,
        "task.grade(model)",
    ),
    exercise(
        "Drill 2 — Early stopping on purpose",
        "Same small-data setup, slightly higher bar. Track validation accuracy each epoch and "
        "**keep the best weights** (restore them before grading), not the final ones.",
        "task = pu.fashion_subset_task(k=4, train_per_class=200, threshold=0.80)\ntask.describe()",
        "train_loader, test_loader = task.loaders()\n"
        "model = nn.Sequential(nn.Flatten(), nn.Linear(28*28, task.n_classes))  # TODO: train, snapshot best, restore",
        REG_SOL,
        "task.grade(model)",
    ),
]

# ======================================================================================
# Notebook 07 — Capstone practice (open-ended, harder draws)
# ======================================================================================
nb07 = [
    exercise(
        "Capstone drill — Maximize accuracy on a hard subset",
        "A tough **5-class** draw with a higher bar (**86%**). Bring everything: a solid CNN "
        "(BatchNorm), regularization (dropout / weight decay), enough epochs, and early "
        "stopping. Iterate until you pass — then re-run the task cell and do it again with a "
        "new set of classes.\n\n"
        "**Checklist:** ☐ CNN with ≥2 conv blocks ☐ BatchNorm ☐ dropout/weight-decay ☐ "
        "track val acc per epoch ☐ keep best weights ☐ ≥ 86% on the hidden test.",
        "task = pu.fashion_subset_task(k=5, train_per_class=1000, threshold=0.86)\ntask.describe()",
        "train_loader, test_loader = task.loaders()\n"
        "model = nn.Sequential(nn.Flatten(), nn.Linear(28*28, task.n_classes))  # TODO: your best pipeline",
        REG_SOL,
        "task.grade(model)",
    ),
]


def main():
    build("01_tensors_autograd.ipynb", "Practice 01 — Tensors & Autograd",
          "Quick, randomized drills for shapes, broadcasting, autograd, and a first "
          "by-hand gradient descent. Every run draws new numbers.", nb01,
          outro="✅ When you can pass all five on several fresh draws, you own tensors & "
                "autograd. → `02_gradient_descent.ipynb`")
    build("02_gradient_descent.ipynb", "Practice 02 — Gradient Descent",
          "Minimize hidden quadratics by hand and with `torch.optim`, and learn to feel the "
          "learning rate. Fresh hidden minimizers each draw.", nb02,
          outro="✅ Next: turn descent into real model-fitting. → `03_linear_regression.ipynb`")
    build("03_linear_regression.ipynb", "Practice 03 — Linear Regression",
          "Train models to recover **different hidden relationships** each run — single- and "
          "multi-feature, with feature scaling.", nb03,
          outro="✅ Next: classification. → `04_classification.ipynb`")
    build("04_classification.ipynb", "Practice 04 — Classification",
          "Train MLP classifiers on freshly generated blobs and moons — different class "
          "counts and shapes every draw.", nb04,
          outro="✅ Next: images. → `05_cnns.ipynb`")
    build("05_cnns.ipynb", "Practice 05 — CNNs on Images",
          "Build and train CNNs on **random subsets of FashionMNIST** — a different "
          "classification problem each draw.", nb05,
          outro="✅ Next: make training *generalize*. → `06_training_techniques.ipynb`")
    build("06_training_techniques.ipynb", "Practice 06 — Training Techniques",
          "Beat overfitting with regularization and early stopping on small-data draws.", nb06,
          outro="✅ Next: the capstone drill. → `07_capstone.ipynb`")
    build("07_capstone.ipynb", "Practice 07 — Capstone Drill",
          "Open-ended: squeeze the most accuracy out of a hard random subset, using the whole "
          "toolkit. Repeat with new classes to build real intuition.", nb07,
          outro="🎓 Pass several hard draws and you're genuinely fluent. Bring this workflow to "
                "the capstone in `../07-capstone/`.")


if __name__ == "__main__":
    main()
