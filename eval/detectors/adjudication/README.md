# Blind adjudication of held-out disagreements

After the first (and only) measurement of the detectors on the frozen held-out set, every case/detector pair where
a detector disagreed with its label (22 pairs) was re-labelled blind: a language-model reviewer, given only the
written label definitions, the task repository and the patch, decided each pair. It was not told the original
label, the detector's output, or which pairs were disputed: the 22 disputed pairs were shuffled together with 22
randomly drawn agreed pairs for the same detectors as controls.

- `items.yaml`: what the reviewer saw (no labels).
- `answers.yaml`: the reviewer's labels and reasons.
- `key.json`: which item is which case, disputed or control, and the original label.

Result: the reviewer upheld the original label on 22 of 22 disputed pairs and 22 of 22 controls, so no held-out
label was changed (see `../CHANGES.md`). The disagreements are detector errors, and the held-out numbers stand.
The reviewer is a language-model session, not a person.
