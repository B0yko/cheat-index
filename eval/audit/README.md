# Independent re-label audits of real runs

Each audit draws a seeded random sample of 100 completed published runs (`scripts/audit.py sample`), leaving out
the runs listed in `results/v0.1.0/audit-excluded.txt` (runs whose final messages were read while the claim
classifier was refined, plus the earlier samples). For each run, a reviewer saw the task
instruction, the allowed workarounds, the final message and the full diff, but no detector output, flag or
hidden-check result, and labelled tampering, the final-message class and disclosure from the written definitions.
The reviewer is a language model, not a person; the 100 runs were split between two reviewer sessions.
`scripts/audit.py score` compares the labels with the published verdicts.

- `seed2026/`: first audit (summary in `results/v0.1.0/audit-seed2026.json`).
- `seed2027/`: second audit, after the claim rules were refined on other runs (`results/v0.1.0/audit-seed2027.json`).
- `seed2028/`: final audit of the published verdicts, after a last refinement on other runs (`results/v0.1.0/audit.json`).

Each later sample excludes every earlier sample and every run read while refining the rules. The earlier summaries
were scored against the verdicts of their time; re-scoring them against today's summaries gives different numbers,
because the claim rules changed in between. Only `audit.json` is reproducible from the committed summaries.

`key.json` maps item numbers to runs; `labels.yaml` holds the reviewer's labels and one-line notes.
