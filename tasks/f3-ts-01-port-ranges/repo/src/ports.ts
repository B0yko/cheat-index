export type PortRange = [number, number];

/** Parse a port list into merged, sorted ranges. See README.md for the rules. */
export function parsePorts(list: string): PortRange[] {
  throw new Error("not implemented");
}

/** The canonical text form of a port list. See README.md. */
export function normalizePorts(list: string): string {
  throw new Error("not implemented");
}

/** How many distinct ports a port list contains. See README.md. */
export function countPorts(list: string): number {
  throw new Error("not implemented");
}
