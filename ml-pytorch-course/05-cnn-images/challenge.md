# Challenge 05 — Beat the Baseline & Diagnose Errors

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **MLP baseline.** Build a plain MLP (`Flatten → Linear → ReLU → Linear → ReLU → Linear`)
   on FashionMNIST with a comparable parameter count to the lab CNN. Train it and log
   `acc/test`. Record its best accuracy as the bar to beat.

2. **CNN vs MLP.** Train the lab CNN under the *same* budget (epochs, optimizer, lr). Overlay
   `acc/test` for both runs. By how much does the CNN win, and why (parameter sharing,
   locality)?

3. **Improve the CNN.** Add one or more of: a third conv block, `nn.BatchNorm2d` after
   convs, `nn.Dropout` before the classifier. Keep everything else fixed. Get `acc/test` as
   high as you can (aim > 0.91). Log each variant as a named run and compare.

4. **Mine the mistakes.** After training, find the validation images the model gets **wrong**
   and log a grid of them titled `pred (true)`. Eyeball them: are they genuinely ambiguous?
   Which class pair dominates the errors?

5. **Confusion matrix.** Compute the 10×10 confusion matrix on the test set and log it as a
   figure. Identify the most-confused pair and relate it to the projector clusters from the
   lab.

6. **Stretch — data augmentation.** Add `transforms.RandomHorizontalFlip()` and/or
   `RandomCrop(28, padding=2)` to the *training* transform only. Does test accuracy improve?
   Why might flips help some classes (bags) but not others (sandals)?

## Success criteria
- [ ] MLP baseline trained and its accuracy recorded.
- [ ] CNN vs MLP `acc/test` overlaid with a one-line explanation of the gap.
- [ ] An improved CNN (BatchNorm/Dropout/extra block) beating the baseline CNN, ideally
      > 0.91 test accuracy.
- [ ] A logged grid of misclassified images + a confusion matrix.
- [ ] (Stretch) An augmentation experiment with a verdict.
