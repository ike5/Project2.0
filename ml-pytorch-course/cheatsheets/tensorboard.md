# TensorBoard cheatsheet

How to write logs from PyTorch and read them in the dashboard.

## Launch the dashboard

```bash
tensorboard --logdir runs                 # point at the parent of your run folders
tensorboard --logdir runs --port 6007     # different port
tensorboard --logdir runs --bind_all      # expose on a remote host
# then open http://localhost:6006
```

> `--logdir` should be the *parent* directory. Each subfolder under it is one **run** and
> shows up as a separate, toggleable line/series.

## Create a writer

```python
from torch.utils.tensorboard import SummaryWriter

# Give each experiment a distinct subfolder so runs don't overwrite each other:
writer = SummaryWriter(log_dir="runs/exp1_lr0.1")
# ... log things ...
writer.flush()     # force-write buffered events (handy mid-run)
writer.close()     # at the end
```

A naming convention that pays off later:

```python
from datetime import datetime
name = f"runs/mlp_lr{lr}_bs{bs}_{datetime.now():%m%d_%H%M%S}"
writer = SummaryWriter(name)
```

## Scalars — the line charts (loss, acc, lr)

```python
writer.add_scalar("loss/train", loss.item(), global_step)
writer.add_scalar("loss/val",   val_loss,    global_step)
writer.add_scalar("acc/val",    val_acc,     global_step)
writer.add_scalar("lr",         opt.param_groups[0]["lr"], global_step)

# Several series on ONE chart:
writer.add_scalars("loss", {"train": tr, "val": va}, global_step)
```
The `tag` uses `/` to group: everything under `loss/` lands in a "loss" section.

## Histograms — distributions over time (weights & gradients)

```python
for name, p in model.named_parameters():
    writer.add_histogram(f"weights/{name}", p, global_step)
    if p.grad is not None:
        writer.add_histogram(f"grads/{name}", p.grad, global_step)
```
Read them to spot **vanishing** (grads collapsing to 0) or **exploding** (blowing up)
gradients, and to watch weights spread out as the model learns.

## Model graph

```python
example = torch.randn(1, 1, 28, 28)        # one dummy input of the right shape
writer.add_graph(model, example)
```

## Images

```python
from torchvision.utils import make_grid
imgs, _ = next(iter(loader))
writer.add_image("inputs", make_grid(imgs[:16], nrow=4), global_step)
# single image tensor is (C,H,W); a batch grid via make_grid
```

## Matplotlib figures (e.g. the gradient-descent path)

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.contour(W1, W2, Z, levels=30)
ax.plot(path_w1, path_w2, "o-", color="red")     # the descent trajectory
writer.add_figure("descent/path", fig, global_step)
plt.close(fig)
```

## Hyperparameters (compare runs)

```python
writer.add_hparams(
    {"lr": lr, "batch_size": bs, "optimizer": "adam"},   # the config
    {"hparam/val_acc": best_acc, "hparam/val_loss": best_loss},  # the results
)
```
Use the **HPARAMS** tab to sort runs by metric and find the best config.

## Embeddings (the projector)

```python
writer.add_embedding(features, metadata=labels, label_img=images, global_step=step)
```

## Reading the dashboard

- **SCALARS** — line charts; the **smoothing** slider only affects the view, not the data.
  Toggle individual runs in the left panel; hover for exact values.
- **HISTOGRAMS / DISTRIBUTIONS** — same data, two views (ridgeline vs percentile bands).
- **GRAPHS** — double-click nodes to expand the model.
- **IMAGES** — a step slider scrubs through logged images over time.
- **HPARAMS** — table + parallel-coordinates + scatter to compare configs.

## Tips & gotchas

- **One writer per run.** Reusing a folder appends and can tangle steps; use a fresh
  `log_dir` per experiment.
- **Pass a `global_step`** to every call so the x-axis is meaningful and curves align.
- **`.item()` your scalars** — log Python floats, not graph-attached tensors.
- **`flush()`** if you want to see data before the script ends (long runs).
- **Stale charts?** TensorBoard caches; hit the refresh icon (top-right) or set
  `--reload_interval 5`.
- **Clean slate:** delete the `runs/` folder (or specific subfolders) to clear old
  experiments.
