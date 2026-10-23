# 5. Task-cluster bootstrap intervals and rank groups

Status: accepted

## Context
Runs of the same task are correlated: an agent that cheats on a task tends to cheat on every repeat of it.
Treating runs as independent would make intervals too narrow. With 30 tasks behind each headline number, many
differences between configurations are within noise, and a ranked list would overstate them.

## Decision
Every rate gets a 95% percentile interval from a bootstrap that resamples tasks with replacement (10,000
resamples, fixed seed) and pools all runs of the drawn tasks. Detail pages add Wilson intervals on per-family k/N.
The leaderboard sorts by the ACI point estimate and forms rank groups greedily: the first configuration opens a
group; each next one joins the current group unless its interval does not overlap the interval of the group's first
member, in which case it opens a new group. Prose that orders two configurations is generated only when a paired
task-cluster bootstrap of their difference (same tasks, 10,000 resamples) gives a 95% interval excluding zero.

## Consequences
- Configurations in one rank group are presented as not distinguishable at this sample size.
- Both rules are unit-tested (`tests/test_metrics.py`).
