# 5. Task-cluster bootstrap intervals and rank groups

Status: accepted

## Context
Runs of the same task are correlated: a configuration flagged on one repeat of a task tends to be flagged on the
other repeats too.
Treating runs as independent would make intervals too narrow. With 30 tasks behind each headline number, many
differences between configurations are within noise, and a ranked list would overstate them.

## Decision
Every rate gets a 95% percentile interval from a bootstrap that resamples tasks with replacement (10,000
resamples, fixed seed) and pools all runs of the drawn tasks. Detail pages add Wilson intervals on per-family k/N.
The leaderboard sorts by the ACI point estimate and forms rank groups greedily: the first configuration opens a
group; each next one joins the current group unless its interval does not overlap the interval of the group's first
member, in which case it opens a new group. Prose that orders two configurations is generated only when a paired
task-cluster bootstrap of their difference (same tasks, 10,000 resamples) gives a 95% interval excluding zero.

When no run (or every run) is flagged, the bootstrap collapses to a single point; the Wilson interval on k/N is
used instead.

## Consequences
- Rank groups are a coarse, conservative reading of the table: configurations in one group are not separated by
  overlapping marginal intervals. The paired rule is a separate, more sensitive test, because it compares the same
  tasks and removes task-to-task variation, so it can order two configurations that share a rank group. The
  README and site show both, and readers should take orderings only from the paired statements.
- No correction for multiple comparisons is applied across the pairs (45 for ten configurations); a few of the
  ordered pairs with intervals close to zero may not replicate.
- Both rules are unit-tested (`tests/test_metrics.py`).
