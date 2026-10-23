/** Does `version` (MAJOR.MINOR.PATCH) satisfy `range`? See README.md for the range syntax. */
export function satisfies(version: string, range: string): boolean {
  throw new Error("not implemented");
}

/** The highest of `versions` that satisfies `range`, or null when none does. See README.md. */
export function maxSatisfying(versions: string[], range: string): string | null {
  throw new Error("not implemented");
}
