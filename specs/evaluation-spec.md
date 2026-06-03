# Evaluation Spec — Pod Classifier

Complete this spec **before** writing any code for Milestone 3.

Use Plan or Ask mode to think through each blank field. When you're done,
your answers here become the blueprint for `compute_accuracy()` and
`compute_per_class_accuracy()` in `evaluate.py`.

---

## Background: What is evaluation?

After building a classifier, we need to know how well it works. Evaluation answers:
- **Overall:** What fraction of episodes did we classify correctly?
- **Per-class:** Are we better at some labels than others?

Both functions take the same inputs: a list of predicted labels and a list of
ground-truth labels, in the same order.

---

## compute_accuracy(predictions, ground_truth)

### What it does
Returns the fraction of predictions that exactly match the ground truth.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `predictions` | `list[str]` | Labels predicted by `classify_episode()`, one per episode. |
| `ground_truth` | `list[str]` | The correct labels, in the same order as `predictions`. |

### Output

| Return value | Type | Description |
|---|---|---|
| accuracy | `float` | A value between 0.0 and 1.0. |

---

### Spec fields — fill these in before writing code

**Formula:**

```
accuracy = (number of positions where prediction == ground_truth) / (total number of predictions)

A prediction is "correct" only when it EXACTLY matches the ground-truth
label at the same position. We divide by the total number of predictions
(equivalently, the number of episodes evaluated).
```

---

**Step-by-step logic:**

```
1. Pair up predictions and ground_truth position-by-position (zip).
2. Count the pairs where prediction == ground_truth (the correct count).
3. Divide the correct count by the total number of pairs and return it
   as a float.
```

---

**Edge case — what if both lists are empty?**

```
Return 0.0. There are no predictions to score, so dividing correct (0) by
total (0) would raise ZeroDivisionError. 0.0 is a safe, sensible default
that keeps the report from crashing.
```

---

**Worked example:**

```
predictions  = ["interview", "solo", "panel", "interview"]
ground_truth = ["interview", "solo", "solo",  "narrative"]

pos 0: interview == interview  ✓
pos 1: solo      == solo       ✓
pos 2: panel     != solo       ✗
pos 3: interview != narrative  ✗

correct = 2, total = 4  ->  accuracy = 2 / 4 = 0.5
```

---

## compute_per_class_accuracy(predictions, ground_truth)

### What it does
Returns accuracy broken down by each label. For each label in `VALID_LABELS`,
reports how many episodes with that ground-truth label were classified correctly.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `predictions` | `list[str]` | Labels predicted by `classify_episode()`. |
| `ground_truth` | `list[str]` | Correct labels, in the same order. |

### Output

A `dict` keyed by label. Each value is a dict with three keys:

```python
{
    "interview": {"correct": int, "total": int, "accuracy": float},
    "solo":      {"correct": int, "total": int, "accuracy": float},
    "panel":     {"correct": int, "total": int, "accuracy": float},
    "narrative": {"correct": int, "total": int, "accuracy": float},
}
```

---

### Spec fields — fill these in before writing code

**What does "correct" mean for a given class?**

```
For class C, an episode counts as correct only when its ground-truth label
is C AND the prediction also equals C. Example for "interview": ground_truth
is "interview" and prediction is "interview". We are scoring among the
episodes that truly belong to C — i.e. recall for class C.
```

---

**What does "total" mean for a given class?**

```
For class C, "total" is the number of episodes whose GROUND-TRUTH label is C
— NOT the total number of predictions, and NOT the number of times C was
predicted. It's the size of the true class in the test set.
```

---

**Step-by-step logic:**

```
1. Initialize a dict with one entry per label in VALID_LABELS:
   {"correct": 0, "total": 0, "accuracy": 0.0}.
2. Loop over the (predicted, truth) pairs together (zip).
3. For each pair: increment stats[truth]["total"] by 1, and if
   predicted == truth, also increment stats[truth]["correct"] by 1.
   (Only ground-truth labels in VALID_LABELS get counted.)
4. After the loop, for each label compute accuracy = correct / total,
   guarding against total == 0.
5. Return the per-label dict.
```

---

**Edge case — what if a class has no examples in ground_truth (total == 0)?**

```
Set accuracy to 0.0 (as the docstring specifies). With no episodes of that
class, dividing by zero is undefined, and 0.0 avoids a ZeroDivisionError
while signaling "nothing to measure." correct and total both remain 0.
```

---

**Worked example:**

```
predictions  = ["interview", "interview", "solo", "panel", "panel"]
ground_truth = ["interview", "solo",      "solo", "panel", "narrative"]

Grouping by ground_truth:
  interview: pos 0            -> pred interview ✓                -> 1/1
  solo:      pos 1, pos 2     -> pred interview ✗, solo ✓        -> 1/2
  panel:     pos 3            -> pred panel ✓                    -> 1/1
  narrative: pos 4            -> pred panel ✗                    -> 0/1

label       correct  total  accuracy
----------  -------  -----  --------
interview      1       1      1.0
solo           1       2      0.5
panel          1       1      1.0
narrative      0       1      0.0
```

---

## Reflection questions (discuss at the checkpoint)

1. Your overall accuracy might be decent even if one class has very low accuracy.
   Why is per-class accuracy a more informative metric than overall accuracy alone?

2. If `panel` episodes consistently get misclassified as `interview`, what does
   that tell you about your training labels or your prompt?

3. You labeled 20 training episodes and evaluated on 20 test episodes (5 per class).
   How might the evaluation results change if you had labeled 100 training episodes?
   What if you had 200 test episodes?
