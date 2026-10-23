export interface FormatOptions {
  binary?: boolean;
  digits?: number;
}

/** Parse a size such as "1.5 kB" into bytes. See README.md for the units. */
export function parseSize(text: string): number {
  throw new Error("not implemented");
}

/** Format a byte count such as 1500 as "1.5 kB". */
export function formatSize(bytes: number, options: FormatOptions = {}): string {
  throw new Error("not implemented");
}
