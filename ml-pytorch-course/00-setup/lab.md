# Lab 00 — Setup & First Tensor

**You'll:** confirm the install, see your device, and watch a curve appear in TensorBoard.
⏱️ ~20 min. Run from the `ml-pytorch-course` folder with your venv active.

---

## Part A — Versions & device

```bash
python 00-setup/code/verify_install.py
```
✅ You see version lines, a `Using device: cpu` (or `cuda`/`mps`) line, and `autograd OK ✅`.
If torchvision/tensorboard show "NOT INSTALLED", re-run `pip install -r requirements.txt`.

## Part B — Poke at tensors in the REPL

```bash
python
```
```python
>>> import torch
>>> x = torch.arange(12.).reshape(3, 4)
>>> x.shape, x.dtype, x.device
>>> x.mean(), x.sum(dim=0)          # reduce all / down columns
>>> (x * 2 + 1)[0]                  # broadcasting + indexing
>>> torch.manual_seed(0); torch.randn(2, 2)
>>> exit()
```
✅ You can predict each `.shape` before pressing Enter. That instinct is most of PyTorch.

## Part C — One gradient by hand

```python
>>> import torch
>>> w = torch.tensor(0.0, requires_grad=True)
>>> loss = (w - 3) ** 2
>>> loss.backward()
>>> w.grad            # tensor(-6.)
```
✅ The gradient is `-6`. Because it's negative, *increasing* `w` lowers the loss — the seed
of gradient descent.

## Part D — The TensorBoard pipeline

```bash
python 00-setup/code/hello_tensorboard.py
tensorboard --logdir runs
```
Open the printed URL (default <http://localhost:6006>).
✅ The **SCALARS** tab shows `demo/sine` (a wave) and `demo/linear` (a ramp). Drag the
**smoothing** slider to 0 to see raw values; hover to read exact points.

> Port in use? `tensorboard --logdir runs --port 6007`.
> Remote machine? `tensorboard --logdir runs --bind_all` and use SSH forwarding.

## Cleanup (optional)

```bash
rm -rf runs/hello        # remove just this demo run
```

---

✅ **Done when:** the verify script prints `autograd OK`, and you've seen a curve in
TensorBoard that your own code produced.

**Next →** [Module 01: Tensors & Autograd](../01-tensors-autograd/)
