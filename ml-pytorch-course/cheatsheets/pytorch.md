# PyTorch cheatsheet

Everything you reach for in this course, in one place.

## Tensors — create

```python
import torch
torch.tensor([1., 2., 3.])          # from data (infers dtype)
torch.zeros(3, 4); torch.ones(2)    # filled
torch.full((2, 2), 7.0)             # constant
torch.arange(0, 10, 2)              # 0,2,4,6,8
torch.linspace(0, 1, 5)             # 5 evenly spaced
torch.randn(3, 4)                   # standard normal
torch.rand(3, 4)                    # uniform [0,1)
torch.eye(3)                        # identity
torch.from_numpy(np_array)          # share memory w/ NumPy
x.clone()                           # copy
torch.manual_seed(0)                # reproducibility
```

## Tensors — inspect & change shape

```python
x.shape          # torch.Size([...])   x.ndim   x.numel()
x.dtype          # torch.float32        x.device  # cpu/cuda/mps
x.reshape(2, 6)  # new shape, same data            x.view(2, 6)  # same, must be contiguous
x.unsqueeze(0)   # add a dim of size 1 at pos 0    x.squeeze()   # drop size-1 dims
x.permute(1, 0)  # reorder dims (transpose general) x.T          # 2-D transpose
x.flatten(1)     # flatten dims from 1 onward
x.to(torch.float32); x.float(); x.long()           # dtype casts
x.to('cuda'); x.cpu()                              # move device
```

## Math & reductions

```python
a + b, a * b, a @ b      # elementwise +,*  and matrix multiply (@)
torch.matmul(a, b); a.dot(b)
x.sum(); x.mean(); x.std(); x.max(); x.min()
x.sum(dim=0)             # reduce along a dim (keepdim=True to keep it)
x.argmax(dim=1)          # index of max — common for classification preds
torch.exp(x); torch.log(x); torch.sqrt(x); x.pow(2)
x.clamp(min=0)           # = ReLU
```

## Broadcasting

```python
A = torch.randn(4, 3)
b = torch.randn(3)       # treated as (1,3) → applies to every row
A + b                    # shapes align from the right; size-1 dims stretch
```

## Autograd

```python
w = torch.tensor(2.0, requires_grad=True)
loss = (w * 3 - 6) ** 2
loss.backward()          # fills w.grad with d loss / d w
w.grad                   # the gradient

with torch.no_grad():    # no graph tracking (eval / manual updates)
    w -= 0.1 * w.grad
w.grad.zero_()           # clear before next step (grads accumulate!)

y = x.detach()           # cut from graph
```

## `nn` — build a model

```python
import torch.nn as nn

model = nn.Sequential(
    nn.Linear(in_features=10, out_features=32),
    nn.ReLU(),
    nn.Linear(32, 1),
)

# or subclass for full control:
class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(10, 32)
        self.fc2 = nn.Linear(32, 1)
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        return self.fc2(x)

model = Net()
model.parameters()       # the learnable tensors
sum(p.numel() for p in model.parameters())   # param count
```

Common layers / losses / activations:

```python
nn.Linear, nn.Conv2d, nn.MaxPool2d, nn.Flatten, nn.Dropout, nn.BatchNorm2d
nn.ReLU, nn.Sigmoid, nn.Tanh, nn.Softmax
nn.MSELoss()             # regression
nn.CrossEntropyLoss()    # classification (takes logits + int labels)
nn.BCEWithLogitsLoss()   # binary (takes logits)
```

## Optimizers

```python
import torch.optim as optim
opt = optim.SGD(model.parameters(), lr=0.1, momentum=0.9, weight_decay=1e-4)
opt = optim.Adam(model.parameters(), lr=1e-3)

opt.zero_grad()          # clear old grads
loss.backward()          # compute grads
opt.step()               # apply update
```

LR schedulers:

```python
sched = optim.lr_scheduler.StepLR(opt, step_size=10, gamma=0.5)
sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=50)
sched.step()             # once per epoch (usually)
sched.get_last_lr()
```

## The canonical training loop

```python
for epoch in range(num_epochs):
    model.train()
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        opt.zero_grad()
        preds = model(xb)
        loss = loss_fn(preds, yb)
        loss.backward()
        opt.step()

    model.eval()
    with torch.no_grad():
        for xb, yb in val_loader:
            ...             # accumulate val loss / accuracy
```

## Data

```python
from torch.utils.data import TensorDataset, DataLoader, random_split
ds = TensorDataset(X, y)
train_ds, val_ds = random_split(ds, [0.8, 0.2])
loader = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=2)

from torchvision import datasets, transforms
tf = transforms.Compose([transforms.ToTensor(),
                         transforms.Normalize((0.5,), (0.5,))])
train = datasets.FashionMNIST('data', train=True, download=True, transform=tf)
```

## Save / load

```python
torch.save(model.state_dict(), 'model.pt')
model.load_state_dict(torch.load('model.pt'))
model.eval()
```

## Device pattern (CPU/GPU agnostic)

```python
device = ('cuda' if torch.cuda.is_available()
          else 'mps' if torch.backends.mps.is_available()
          else 'cpu')
model.to(device)
```

## Gotchas

- **Forgot `opt.zero_grad()`** → gradients accumulate across steps; training goes haywire.
- **`loss.item()`** to read a Python float (don't keep the graph-attached tensor in lists).
- **`model.eval()` + `torch.no_grad()`** for validation — disables dropout/batchnorm
  updates and graph tracking.
- **Shapes:** `CrossEntropyLoss` wants logits `(N, C)` and integer labels `(N,)` — *not*
  one-hot.
- **Float vs long:** features `float32`, class labels `int64` (`long`).
