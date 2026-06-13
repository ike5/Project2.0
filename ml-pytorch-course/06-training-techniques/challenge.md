# Challenge 06 — A Disciplined Training Pipeline

Solutions in [`solutions/`](./solutions/). Try first. This challenge builds the reusable
loop you'll extend in the capstone.

## Tasks

1. **Reusable `train()` function.** Write a single `train(config, ...)` that takes a config
   dict (`lr`, `weight_decay`, `dropout`, `optimizer`, `scheduler`, `epochs`) and:
   - logs `loss/train`, `loss/val`, `acc/train`, `acc/val`, and `lr` each epoch,
   - applies the chosen LR scheduler,
   - implements **early stopping with patience** (stop if val loss hasn't improved for `k`
     epochs) and keeps the **best** model state,
   - finishes with `add_hparams(config, {best_val_acc, best_val_loss})`.

2. **Baseline vs regularized vs scheduled.** Run three configs on a subset of FashionMNIST:
   (a) no regularization, (b) + dropout + weight decay, (c) + a cosine LR schedule. Overlay
   `acc/val` and report which generalizes best.

3. **Early-stopping proof.** Show, from the logs, that config (a) would benefit from early
   stopping — i.e. its best val loss occurs well before the last epoch — and that your loop
   restored the best (not final) weights.

4. **Small grid → HPARAMS.** Sweep at least `weight_decay ∈ {0, 1e-4, 1e-3}` ×
   `dropout ∈ {0, 0.3}` and pick the best by val accuracy from the HPARAMS table.

5. **Save & reload the best model.** `torch.save(best_state, "best.pt")`, build a fresh
   model, `load_state_dict`, and confirm it reproduces the same val accuracy.

6. **Stretch — augmentation.** Add train-time `RandomCrop(28, padding=2)` and compare val
   accuracy with/without. Does more "effective data" reduce the train/val gap?

## Success criteria
- [ ] One `train(config)` function used for every run (no copy-paste loops).
- [ ] Early stopping with patience + best-weight restoration, demonstrated from the logs.
- [ ] Three configs overlaid with a generalization verdict.
- [ ] A small grid compared in the HPARAMS tab; best config identified.
- [ ] Best model saved, reloaded, and verified to match.
