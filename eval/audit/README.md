# Independent re-label audits of real runs

Each audit draws a seeded random sample of 100 completed published runs (`scripts/audit.py sample`), leaving out
the runs listed in `results/v0.1.0/audit-excluded.txt` (runs whose final messages were read while the claim
classifier was refined, plus, for the second audit, the whole first sample). For each run, a reviewer saw the task
instruction, the allowed workarounds, the final message and the full diff, but no detector output, flag or
hidden-check result, and labelled tampering, the final-message class and disclosure from the written definitions.
The reviewer is a language-model session separate from the one that wrote the detectors; the 100 runs were split
between two such sessions. `scripts/audit.py score` compares the labels with the published verdicts.

- `seed2026/`: first audit, before the classifier's last refinement (summary in `results/v0.1.0/audit-seed2026.json`).
- `seed2027/`: final audit of the published verdicts (`results/v0.1.0/audit.json`).

`key.json` maps item numbers to runs; `labels.yaml` holds the reviewer's labels and one-line notes.
