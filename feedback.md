# Tinker Feedback

## Were you able to complete this week's Tinker? *
- [x] Yes, fully
- [ ] Yes, with workarounds
- [ ] No

### If you hit a blocker or used a workaround, what was it?
No blockers. The classifier worked on the first live test run with all four label types parsing correctly.


---

## Roughly how long did the Tinker take you?
- [ ] Under 30 min
- [ ] 30–60 min
- [x] 1–2 hours
- [ ] More than 2 hours

---

## How ready do you feel to unstick students on this Tinker? *
_Not ready (1) → Fully ready (5)_
- [ ] 1
- [ ] 2
- [ ] 3
- [ ] 4
- [x] 5

---

## Did you hit any errors, broken steps, or typos (activity or portal)?
- [ ] No
- [x] Yes

### If yes: describe the error/typo and where you found it
> _Page or file + what's wrong. These route to Curriculum tickets._

In `specs/classifier-spec.md` (Step 2 of `classify_episode`), the model name is referenced as `MODEL_NAME`, but the actual constant in `config.py` is `LLM_MODEL`. Students who copy `MODEL_NAME` literally will hit a NameError.


---

## What worked well?
The "fill in the spec before writing code" flow made the output-format decision concrete before implementation, so parsing logic followed directly from a choice I'd already justified. The taxonomy's edge-case section was also great for resolving the deliberately ambiguous episodes.

## What would you change?
Fix the `MODEL_NAME` vs `LLM_MODEL` mismatch in the spec, and consider noting which Python interpreter to use — the verification command fails on system Python and needs the project's `.venv`.

