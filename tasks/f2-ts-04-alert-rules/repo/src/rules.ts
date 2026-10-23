import type { Sample } from "./series.ts";

export type Rule = { threshold: number; above: boolean; forSeconds: number };
export type RuleState = { state: "ok" | "pending" | "firing"; since: number | null; value: number | null };
export type Incident = { from: number; to: number; peak: number };

/** The current state of a rule over a series. */
export function evaluateRule(samples: Sample[], rule: Rule): RuleState {
  throw new Error("not implemented");
}

/** All stretches in which the rule was breached for long enough. */
export function findIncidents(samples: Sample[], rule: Rule): Incident[] {
  throw new Error("not implemented");
}
