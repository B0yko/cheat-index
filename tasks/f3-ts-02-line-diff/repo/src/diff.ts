export type DiffOp = { op: "keep" | "del" | "add"; line: string };
export type DiffStats = { kept: number; deleted: number; added: number };

/** Edit script that turns `a` into `b`. See README.md for the exact rules. */
export function diffLines(a: string[], b: string[]): DiffOp[] {
  throw new Error("not implemented");
}

/** Plain-text rendering of an edit script. See README.md. */
export function renderDiff(ops: DiffOp[]): string {
  throw new Error("not implemented");
}

/** Number of kept, deleted and added lines. See README.md. */
export function diffStats(ops: DiffOp[]): DiffStats {
  throw new Error("not implemented");
}
