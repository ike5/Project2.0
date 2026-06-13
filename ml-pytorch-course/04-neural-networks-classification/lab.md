# Lab 04 — Train an MLP & Watch the Boundary Form

**You'll:** train a neural net classifier, watch its decision boundary curve into shape, read
weight/gradient histograms, and compare activations. ⏱️ ~60 min. Keep
`tensorboard --logdir runs` open.

---

## Part A — Train the MLP

```bash
python 04-neural-networks-classification/code/mlp_classify.py
tensorboard --logdir runs
```
✅ Final val accuracy ≈ 0.96. **SCALARS:** `loss/train` & `loss/val` fall; `acc/val` climbs
toward ~0.96. Note loss and accuracy aren't perfectly in step — loss is what's optimized,
accuracy is what you report.

## Part B — Watch the decision boundary 🌀

**IMAGES** → `boundary`, drag the **step slider**.
✅ Early on the split is nearly straight and misclassifies the moon tips; as epochs pass the
boundary **curves** to wrap each moon. That bend is what the ReLU nonlinearities buy you.

## Part C — Read weight & gradient histograms

Open **HISTOGRAMS** (or **DISTRIBUTIONS**). Find `weights/0.weight` and `grads/0.weight`.
✅ Weights start as a narrow spike (random init) and **spread out** as the model learns.
Gradients are larger early and shrink as training converges — the same "gradient → 0 near
the minimum" story from Module 02, now per-layer.

## Part D — Prove you need the nonlinearity

```bash
python 04-neural-networks-classification/code/mlp_classify.py --no-relu --epochs 40
```
✅ Accuracy stalls around ~0.86 and the boundary stays **straight** — without activations,
stacked linear layers collapse to one linear layer that can't separate the moons. Compare
the `mlp_h32` and `mlp_h32_norelu` boundaries side by side in IMAGES.

## Part E — Capacity matters

```bash
python 04-neural-networks-classification/code/mlp_classify.py --hidden 2 --epochs 80
```
✅ With only 2 hidden units the model is too weak (underfits) — a kinked but crude boundary,
lower accuracy. Then try `--hidden 64`. More capacity fits the moons cleanly (and, on noisy
data, eventually starts to overfit — the topic of Module 06).

## Part F — Activation showdown

```bash
python 04-neural-networks-classification/code/activation_compare.py
```
✅ Console table + overlay `acc/val` across `act_none/sigmoid/tanh/relu`. `none` (linear)
plateaus well below the rest; ReLU/Tanh/Sigmoid all curve the boundary and reach ~0.98.

## Part G — Reflect (3 sentences)

1. Why does removing activations cap the model's accuracy on the moons?
2. What does it mean if `acc/val` rises while `loss/val` is still noisy?
3. In the gradient histograms, what would *vanishing* gradients look like, and why is that
   bad?

---

✅ **Done when:** you've scrubbed the boundary animation and can explain — pointing at the
no-relu run — why nonlinearity is essential.

**Next →** [challenge.md](./challenge.md) then [Module 05](../05-cnn-images/)
