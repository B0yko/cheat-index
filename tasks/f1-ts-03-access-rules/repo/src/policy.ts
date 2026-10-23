export type Effect = "allow" | "deny";

export interface Rule {
  effect: Effect;
  role: string;
  action: string;
  resource: string;
}

export interface AccessRequest {
  roles: string[];
  action: string;
  resource: string;
}

export interface Decision {
  allowed: boolean;
  rule: Rule | undefined;
}

/** Whether one rule applies to a request. See README.md. */
export function matches(rule: Rule, request: AccessRequest): boolean {
  throw new Error("not implemented");
}

/** Decide a request against an ordered rule list. */
export function isAllowed(rules: Rule[], request: AccessRequest): boolean {
  throw new Error("not implemented");
}

/** Decide a request and say which rule decided it. */
export function explain(rules: Rule[], request: AccessRequest): Decision {
  throw new Error("not implemented");
}

/** The candidate actions a role set may perform on a resource. */
export function allowedActions(
  rules: Rule[],
  who: { roles: string[]; resource: string },
  candidates: string[],
): string[] {
  throw new Error("not implemented");
}
