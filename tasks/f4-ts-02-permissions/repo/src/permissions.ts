import type { Policy } from "./types.ts";

/** May a user holding `roles` perform `action` on `resource`? See README.md. */
export function isAllowed(policy: Policy, roles: string[], action: string, resource: string): boolean {
  throw new Error("not implemented");
}

/** The candidate actions that are allowed on `resource`, in the given order. */
export function allowedActions(policy: Policy, roles: string[], actions: string[], resource: string): string[] {
  throw new Error("not implemented");
}
