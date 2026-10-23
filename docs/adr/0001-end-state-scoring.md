# 1. Score the end state, not the transcript

Status: accepted

## Context
An agent's final message is a claim. Transcripts are long, differ between harnesses and invite judgement calls
about intent. Two runs that end in the same repository state and say the same thing should get the same verdict.

## Decision
Verdicts come from three deterministic sources only: hidden checks run on the final repository state, rule-based
detectors run on the diff between the start state and the end state (plus the egress log), and a rule-based
classifier of the final message. No language model takes part in scoring. The transcript is stored and exported
(agent-trace/v1) so anyone can audit a verdict, but it never decides one.

## Consequences
- Verdicts are reproducible from the recorded diff, final message and hidden-check output (`cheat-index verify`).
- Behaviour that leaves no trace in the end state (for example an agent that edits a test, sees it pass, and then
  restores it) is not counted. We accept this; it is listed under limitations.
- The final-message classifier misreads some messages; its precision and recall on a frozen held-out set are
  published next to the results.
