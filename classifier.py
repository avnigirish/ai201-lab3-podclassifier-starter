import json
import os
from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_LABELS, DATA_PATH, TRAIN_FILE, LABELS_FILE

_client = Groq(api_key=GROQ_API_KEY)


def load_labeled_examples() -> list[dict]:
    """
    Load the training episodes and merge them with the student's labels.

    Returns a list of dicts, each with:
      - "id"          : episode ID
      - "title"       : episode title
      - "podcast"     : podcast name
      - "description" : episode description
      - "label"       : the label from my_labels.json (may be None if not yet annotated)

    Only returns episodes where the label is a valid, non-null string.
    Episodes with null labels are silently skipped.
    """
    train_path = os.path.join(DATA_PATH, TRAIN_FILE)
    labels_path = os.path.join(DATA_PATH, LABELS_FILE)

    with open(train_path, encoding="utf-8") as f:
        episodes = {ep["id"]: ep for ep in json.load(f)}

    with open(labels_path, encoding="utf-8") as f:
        labels = {entry["id"]: entry["label"] for entry in json.load(f)}

    labeled = []
    for ep_id, ep in episodes.items():
        label = labels.get(ep_id)
        if label in VALID_LABELS:
            labeled.append({**ep, "label": label})

    return labeled


_TASK_INSTRUCTION = """You are classifying podcast episodes by their format. Classify the episode into exactly one of these four labels:

- interview: a conversation between a host and one or more guests
- solo: a single host speaking from memory, experience, or opinion — no guests, no assembled external sources
- panel: multiple guests with roughly equal speaking time, often debating or discussing a topic together
- narrative: a story assembled from external sources — interviews, archival audio, reporting — with a clear narrative arc

Classify by the episode's structural format, not its topic or tone. Return only the label and your reasoning. Do not explain the taxonomy."""

_OUTPUT_FORMAT = """Respond in exactly this format, with nothing before or after:

Label: <one of: interview, solo, panel, narrative>
Reasoning: <one or two sentences explaining why>"""


def build_few_shot_prompt(labeled_examples: list[dict], description: str) -> str:
    """
    Build a few-shot classification prompt using the student's labeled training examples.

    Structure (see specs/classifier-spec.md):
      1. Task instruction + the four label definitions
      2. Each labeled example as "Title / Description / Label" blocks, "---" separated
      3. The new episode in the same shape (Label left as "?")
      4. An explicit output-format instruction so the response is parseable

    Handles an empty labeled_examples list gracefully (becomes a zero-shot
    prompt that still relies on the label definitions).
    """
    parts = [_TASK_INSTRUCTION]

    if labeled_examples:
        parts.append("Here are labeled examples:")
        example_blocks = []
        for ex in labeled_examples:
            example_blocks.append(
                f"Title: {ex['title']}\n"
                f"Description: {ex['description']}\n"
                f"Label: {ex['label']}"
            )
        parts.append("\n\n---\n\n".join(example_blocks))

    parts.append(
        "Now classify this episode:\n\n"
        f"Description: {description}\n"
        "Label: ?"
    )
    parts.append(_OUTPUT_FORMAT)

    return "\n\n".join(parts)


def classify_episode(description: str, labeled_examples: list[dict]) -> dict:
    """
    Classify a single podcast episode description using the few-shot LLM classifier.

    Returns a dict with "label" (one of VALID_LABELS, or "unknown") and
    "reasoning". Never raises — on any API or parsing failure it returns an
    "unknown" label so the evaluation loop can complete all 20 calls.
    """
    try:
        prompt = build_few_shot_prompt(labeled_examples, description)

        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
        )
        response_text = response.choices[0].message.content or ""

        # --- Parse: scan lines for the keyed "Label:" / "Reasoning:" format ---
        label = ""
        reasoning = ""
        for line in response_text.splitlines():
            stripped = line.strip()
            lowered = stripped.lower()
            if lowered.startswith("label:") and not label:
                label = stripped.split(":", 1)[1].strip().lower()
            elif lowered.startswith("reasoning:") and not reasoning:
                reasoning = stripped.split(":", 1)[1].strip()

        # Fall back to the full response if no explicit reasoning line was found.
        if not reasoning:
            reasoning = response_text.strip()

        # --- Validate the label ---
        if label not in VALID_LABELS:
            label = "unknown"

        return {"label": label, "reasoning": reasoning}

    except Exception as e:
        return {"label": "unknown", "reasoning": f"Error: {e}"}
