export interface Version {
  major: number;
  minor: number;
  patch: number;
  prerelease: string[];
}

/** Parse a version string. See README.md for the accepted syntax. */
export function parseVersion(text: string): Version {
  throw new Error("not implemented");
}

/** Compare two version strings by precedence. */
export function compareVersions(a: string, b: string): -1 | 0 | 1 {
  throw new Error("not implemented");
}

/** Sort versions in ascending order without changing the input. */
export function sortVersions(versions: string[]): string[] {
  throw new Error("not implemented");
}

/** The highest version without a pre-release part. */
export function latestStable(versions: string[]): string | undefined {
  throw new Error("not implemented");
}
