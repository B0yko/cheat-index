# Label changes to the frozen held-out set

`heldout.yaml` is frozen; its hash is in MANIFEST.sha256. It was written before any detector existed and is never
used for tuning. A label is changed only by an entry here (case id, detector, old label, new label, reason), with
the updated manifest in the same commit.

No label has been changed. The 22 disagreements found at the first measurement were re-labelled blind and all
original labels were upheld; see `adjudication/README.md`.
