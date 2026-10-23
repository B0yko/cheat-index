export type Effect = "allow" | "deny";

export interface Rule {
  effect: Effect;
  actions: string[];
  resources: string[];
}

/** The rules of each role, by role name. */
export type Policy = Record<string, Rule[]>;
