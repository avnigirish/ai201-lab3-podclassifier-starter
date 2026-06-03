# Classifier Spec — Pod Classifier

Complete this spec **before** writing any code for Milestone 2.

Use Plan or Ask mode to think through each blank field. When you're done,
your answers here become the blueprint for `build_few_shot_prompt()` and
`classify_episode()` in `classifier.py`.

---

## build_few_shot_prompt(labeled_examples, description)

### What it does
Constructs a prompt string for the LLM that includes the task instructions,
all labeled training examples, and the new episode description to classify.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `labeled_examples` | `list[dict]` | Each dict has `"title"`, `"description"`, `"label"` (and others). These are the examples you labeled in Milestone 1. |
| `description` | `str` | The episode description to classify. |

### Output

| Return value | Type | Description |
|---|---|---|
| prompt | `str` | A complete prompt string ready to send to the LLM. |

---

### Spec fields — fill these in before writing code

**Task instruction (what should the LLM know about the task?):**

```
You are classifying podcast episodes by their format. Classify the episode
into exactly one of these four labels:

- interview: a conversation between a host and one or more guests
- solo: a single host speaking from memory, experience, or opinion — no guests,
  no assembled external sources
- panel: multiple guests with roughly equal speaking time, often debating or
  discussing a topic together
- narrative: a story assembled from external sources — interviews, archival
  audio, reporting — with a clear narrative arc

Return only the label and your reasoning. Do not explain the taxonomy.
```

---

**How should labeled examples be formatted in the prompt?**

```
Each example should include the episode title, a brief excerpt or the full
description, and the correct label. Separate examples with a blank line or
a delimiter like "---". Include all fields that help the model see why the
label was applied — title and description are both useful; other fields
(like episode ID) are not needed.
```

---

**Example block sketch (write one concrete example):**

```
Title: {title}
Description: {description}
Label: {label}
```

---

**How should the new episode (to be classified) be presented?**

```
Present it in the same format as the labeled examples, but omit the Label
line and replace it with an instruction to classify. For example:

Title: {title}
Description: {description}
Label: ?

Then add a line like: "Classify the episode above. Return your answer in
the format below:" followed by the output format you chose.
```

---

**What output format should you request from the LLM?**

```
DECISION: A keyed two-line format —

    Label: <one of interview|solo|panel|narrative>
    Reasoning: <one or two sentences>

Why this over the alternatives:
- vs. JSON: JSON is clean when valid, but LLMs often wrap it in ```json
  fences, add preamble, or emit invalid JSON (unescaped quotes inside the
  reasoning string). That forces fallback parsing anyway.
- vs. "label alone on the first line": fragile if the model prepends filler
  ("Sure! interview") — you can't tell which token is the label.
- The keyed format is the most parse-TOLERANT: scan lines for the one
  starting with "Label:", take the text after the colon, strip + lowercase,
  and validate. Preamble or extra prose doesn't break it, and even a partial
  response still yields a recoverable label.

Parsing matters more than elegance here: the eval loop calls this 20×, and
one malformed response must not crash the run.
```

---

**Edge cases to handle in the prompt:**

```
- Empty labeled_examples: still emit a valid prompt with the task
  instruction and label definitions (the definitions act as a zero-shot
  fallback), just omit the examples block. Don't crash.
- Very short / thin description: pass it through unchanged. The task
  instruction already tells the model to classify by format; a short
  description simply gives the model less to go on, which is acceptable —
  it can still reason from whatever signal exists.
- Always close the prompt with the explicit output-format instruction so the
  model returns the keyed "Label:" / "Reasoning:" format regardless of how
  many examples were included.
```

---

## classify_episode(description, labeled_examples)

### What it does
Classifies a single podcast episode description using the few-shot LLM classifier.
Returns a dict with a label and reasoning.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `description` | `str` | The episode description to classify. |
| `labeled_examples` | `list[dict]` | Labeled training examples from `load_labeled_examples()`. |

### Output

| Return value | Type | Description |
|---|---|---|
| result | `dict` | Must have keys `"label"` and `"reasoning"`. `"label"` must be one of `VALID_LABELS` or `"unknown"`. |

---

### Spec fields — fill these in before writing code

**Step 1 — Build the prompt:**

```
Call build_few_shot_prompt(labeled_examples, description) and store the
returned string in a variable (e.g., prompt). Pass through both arguments
exactly as received — no modification needed before calling.
```

---

**Step 2 — Send to the LLM:**

```
Call _client.chat.completions.create() with:
  - model: the model name from config (MODEL_NAME)
  - messages: a list with one dict — {"role": "user", "content": prompt}
  - max_tokens: a reasonable limit (e.g., 200–300) to keep responses concise

Extract the response text from:
  response.choices[0].message.content
```

---

**Step 3 — Parse the response:**

```
Split the response text into lines. Scan for the first line whose stripped,
lowercased form starts with "label:" — take the text after the colon, strip
it, lowercase it. That is the candidate label.

For reasoning: find the line starting with "reasoning:" and take the text
after its colon. If no explicit "Reasoning:" line exists, fall back to using
the whole response text (or everything after the label line) as the
reasoning, so we never return an empty explanation.
```

---

**Step 4 — Validate the label:**

```
Check the parsed candidate label against VALID_LABELS (the lowercased,
stripped string must be an exact member). If it matches, use it. If it does
not match — empty, misspelled, capitalized differently after normalization,
or the model returned prose with no parseable label — set label to
"unknown". Never return a label outside VALID_LABELS ∪ {"unknown"}.
```

---

**Step 5 — Handle errors gracefully:**

```
Wrap the API call and parsing in a try/except. Things that can go wrong:
- Network / API error, rate limit, or timeout from Groq.
- Empty or None response content.
- Response with no parseable "Label:" line (handled in Step 4 → "unknown").

On any exception, do NOT raise. Return:
    {"label": "unknown", "reasoning": "Error: <message>"}
so the evaluation loop's 20 calls continue even if one fails. A label of
"unknown" simply counts as an incorrect prediction rather than crashing
the run.
```

---

### Return value structure

```python
{
    "label": str,      # one of VALID_LABELS, or "unknown" if invalid/error
    "reasoning": str,  # brief explanation from the LLM
}
```

---

## Notes on label quality

The classifier is only as good as your labels. If your training examples have
inconsistent or ambiguous labels, the LLM will learn the wrong pattern.

Before implementing the classifier, re-read `data/taxonomy.md` and double-check
any labels you're unsure about. Annotation quality is part of the lab.

---

## Implementation Notes

*Fill this in after implementing and testing both functions.*

**Test: what does the raw LLM response look like for one episode?**

```
Episode tested: "Chef Marco Reyes joins us..." (a host+guest interview description)

Raw response text (exact, via repr()):
'Label: interview\nReasoning: The episode features a conversation between a
host and a single guest, Chef Marco Reyes, discussing his experiences and
opinions, which is characteristic of an interview format. The description
mentions "we ask him" and "he talks", indicating a conversation between the
host and the guest.'

The model returned exactly the requested two-line keyed format — "Label:"
on the first line, "Reasoning:" on the second — with no preamble, no code
fences, and no trailing prose.
```

**How did you parse the label out of the response?**

```
splitlines() over the response, then for each line: strip() it, lower() a
copy, and check str.startswith("label:"). On the first match, take
line.split(":", 1)[1], then .strip().lower() to get the bare label token.
Reasoning is extracted the same way from the "reasoning:" line, with a
fallback to the whole stripped response if no Reasoning line is present.
Finally the label is checked for membership in VALID_LABELS; anything else
becomes "unknown".
```

**Did any episodes return `"unknown"`? If so, why?**

```
No. All four test descriptions (one per label) parsed cleanly and returned
the correct label. The model consistently honored the keyed format, so the
"unknown" path was only exercised by deliberate error/validation handling,
not by real responses.
```

**One thing about the output format that surprised you:**

```
How reliably the 70b model stuck to the exact format — no markdown fences,
no "Sure, here's the classification:" preamble, no extra blank lines. I'd
braced for messier output (which is why the parser scans for the "Label:"
prefix rather than assuming line 1 is the label), and that tolerance turned
out to be insurance I didn't end up needing — but it's cheap and makes the
20-call eval loop robust to the one response that eventually won't conform.
```
