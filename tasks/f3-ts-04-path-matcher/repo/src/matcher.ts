/** Selects paths with an ordered list of glob patterns. See README.md for the syntax. */
export class PathMatcher {
  constructor(patterns: string[]) {
    throw new Error("not implemented");
  }

  /** Whether `path` is selected. */
  matches(path: string): boolean {
    throw new Error("not implemented");
  }

  /** The selected paths, in their original order. */
  filter(paths: string[]): string[] {
    throw new Error("not implemented");
  }

  /** The pattern that decided about `path`, or null when none matches. */
  explain(path: string): string | null {
    throw new Error("not implemented");
  }
}
