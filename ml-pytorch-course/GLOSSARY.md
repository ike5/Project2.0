# Glossary

Plain-English definitions of the PyTorch, math, and TensorBoard terms in this course.

## Core ML ideas

- **Model** — a function with adjustable numbers (**parameters**) that maps inputs to
  predictions. Training = finding good numbers.
- **Parameter / weight** — a number the model learns (e.g. a slope `w` and bias `b`).
  Stored as a tensor with `requires_grad=True`.
- **Loss** — a single number measuring how wrong the model is right now. Smaller = better.
  Also called *cost* or *objective*.
- **Loss function** — the rule that turns predictions + true answers into the loss, e.g.
  **MSE** (regression) or **cross-entropy** (classification).
- **Gradient** — the vector of slopes of the loss with respect to each parameter. It points
  in the direction of **steepest increase**; we step the opposite way.
- **Gradient descent (GD)** — repeatedly: compute the gradient, take a small step
  *downhill*. The whole course is variations on this.
- **Learning rate (lr)** — how big each downhill step is. Too small → slow; too big →
  overshoot/diverge.
- **Epoch** — one full pass over the training dataset.
- **Batch / mini-batch** — a small group of samples processed together; **SGD** uses
  batches instead of the whole dataset per step.
- **Optimizer** — the object that applies the update rule (SGD, Adam, …) given the
  gradients.
- **Convergence** — loss has flattened out; more steps barely help.

## Tensors & autograd

- **Tensor** — PyTorch's n-dimensional array (scalar, vector, matrix, …). Like a NumPy
  array but GPU-capable and gradient-aware.
- **Shape** — the size along each dimension, e.g. `(32, 3, 28, 28)`. Getting shapes right
  is half of PyTorch.
- **dtype** — the element type (`float32`, `int64`, `bool`, …).
- **device** — where a tensor lives: `cpu`, `cuda` (NVIDIA GPU), or `mps` (Apple GPU).
- **`requires_grad`** — flag that tells autograd to track operations on a tensor so it can
  compute gradients later.
- **Autograd** — PyTorch's automatic differentiation engine. It records a **computation
  graph** of your operations and computes exact gradients on `backward()`.
- **`.backward()`** — triggers autograd to fill each parameter's `.grad` with ∂loss/∂param.
- **`.grad`** — where a tensor's accumulated gradient is stored after `backward()`.
- **`zero_grad()`** — clears `.grad` before the next step. Gradients **accumulate** by
  default, so you must zero them each iteration.
- **`torch.no_grad()`** — context that turns off graph tracking (for evaluation/updates),
  saving memory and avoiding accidental gradient tracking.
- **`.detach()`** — returns a tensor cut off from the graph (no gradient flows through).
- **Broadcasting** — automatic shape-matching that lets you combine tensors of different
  but compatible shapes without explicit copies.

## Building models (`torch.nn`)

- **`nn.Module`** — base class for models and layers. Holds parameters and defines a
  `forward()`.
- **Layer** — a reusable building block: `nn.Linear` (fully connected), `nn.Conv2d`
  (convolution), `nn.ReLU` (activation), etc.
- **Forward pass** — running inputs through the model to get predictions.
- **Backward pass** — running autograd to get gradients of the loss.
- **Activation function** — a nonlinearity (ReLU, sigmoid, tanh) that lets stacked layers
  model non-linear relationships.
- **Logits** — raw, unnormalized model outputs *before* softmax/sigmoid.
- **Softmax** — turns logits into a probability distribution over classes.
- **`state_dict`** — a dictionary of a model's parameters; what you save/load to persist a
  model.

## Data

- **`Dataset`** — an object that returns one `(input, label)` sample by index.
- **`DataLoader`** — wraps a `Dataset` to yield shuffled **batches**, optionally with
  multiple worker processes.
- **Transform** — preprocessing applied to samples (e.g. `ToTensor`, normalization).
- **Train / validation / test split** — train to fit, validation to tune, test to report
  final, untouched performance.

## Training dynamics

- **Overfitting** — the model memorizes training data; train loss keeps dropping while
  validation loss rises.
- **Underfitting** — the model is too weak/undertrained; both losses stay high.
- **Regularization** — techniques that fight overfitting: **weight decay** (L2),
  **dropout**, early stopping, data augmentation.
- **Learning-rate schedule** — a plan that changes the lr over training (step decay, cosine,
  warmup).
- **Gradient explosion / vanishing** — gradients grow huge or shrink to ~0, stalling
  learning; watched via weight/grad **histograms**.

## TensorBoard

- **TensorBoard** — a web dashboard that visualizes logs written during training.
- **`SummaryWriter`** — the PyTorch object (`torch.utils.tensorboard`) that writes logs to a
  run directory.
- **Run / `logdir`** — a folder of event files for one experiment; TensorBoard shows many
  runs side by side.
- **Scalar** — a single number logged over steps (loss, accuracy, lr). The bread-and-butter
  line chart. `writer.add_scalar(...)`.
- **Histogram** — the distribution of many values (a layer's weights or gradients) over
  time. `writer.add_histogram(...)`.
- **Graph** — a diagram of your model's computation. `writer.add_graph(...)`.
- **Image** — pictures logged for inspection (input batches, filters, predictions).
  `writer.add_image(...)`.
- **Figure** — a matplotlib figure logged as an image (we use it to draw the GD path).
  `writer.add_figure(...)`.
- **Embedding / projector** — high-dim vectors projected to 2-D/3-D to inspect structure.
- **HParams** — TensorBoard's hyperparameter dashboard comparing runs by config + metric.
  `writer.add_hparams(...)`.
- **Step / global step** — the x-axis counter you pass to logging calls (iteration or
  epoch number).
- **Smoothing** — TensorBoard's UI slider that visually averages noisy curves; it does not
  change your data.
