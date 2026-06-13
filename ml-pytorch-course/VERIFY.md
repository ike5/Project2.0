# VERIFY — confirm your environment works

Run these before Module 01. Each has an expected result. If one fails, the fix is noted.

---

## 1. Python is 3.9+

```bash
python --version
```
✅ `Python 3.9.x` or newer. If `python` is missing, try `python3` (and use `python3`
throughout the course).

## 2. A clean virtual environment (recommended)

```bash
cd ml-pytorch-course
python -m venv .venv
source .venv/bin/activate           # Windows PowerShell: .venv\Scripts\Activate.ps1
```
✅ Your prompt shows `(.venv)`. Everything below installs *into* this sandbox, leaving your
system Python untouched.

## 3. Install the stack

```bash
pip install -r requirements.txt
```
✅ Finishes without errors. This pulls **torch**, **torchvision**, **tensorboard**,
**matplotlib**, **numpy**. First install downloads ~1 GB; be patient.

> Behind a proxy / air-gapped? The CPU wheels are all you need. For CUDA builds, use the
> selector at <https://pytorch.org/get-started/locally/>.

## 4. PyTorch imports and reports a device

```bash
python 00-setup/code/verify_install.py
```
✅ Prints torch/torchvision/tensorboard versions and a line like
`Using device: cpu` (or `cuda` / `mps`). It also runs a 1-line gradient check that prints
`autograd OK ✅`.

## 5. TensorBoard launches

```bash
python 00-setup/code/hello_tensorboard.py     # writes a few scalars to runs/hello
tensorboard --logdir runs
```
Open the URL it prints (default <http://localhost:6006>).
✅ You see a **SCALARS** tab with a `demo/sine` curve. That confirms the full pipeline:
*your code → event files → the dashboard*.

> Port 6006 busy? `tensorboard --logdir runs --port 6007`.
> Running on a remote box? add `--bind_all` and open `http://<host>:6006`, or use SSH port
> forwarding: `ssh -L 6006:localhost:6006 user@host`.

## 6. (Optional) GPU sanity

```bash
python -c "import torch; print('cuda', torch.cuda.is_available()); \
print('mps', getattr(torch.backends,'mps',None) and torch.backends.mps.is_available())"
```
✅ At least one is `True` if you have a supported GPU. **All labs run fine on CPU** — this
is informational only.

---

If 1–5 pass, you're ready. 👉 **[Module 00: Setup & First Tensor](./00-setup/)**
