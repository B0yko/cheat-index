export type Offset = { offsetMinutes: number; abbr: string };
export type Transition = Offset & { at: string };
export type ZoneRules = { zone: string; initial: Offset; transitions: Transition[] };

export class ZoneError extends Error {}

/** Validate the decoded tz service answer. */
export function parseZone(body: unknown): ZoneRules {
  throw new Error("not implemented");
}

/** The offset in force at a UTC instant. */
export function offsetAt(rules: ZoneRules, instant: string): Offset {
  throw new Error("not implemented");
}

/** "+HH:MM" or "-HH:MM". */
export function formatOffset(minutes: number): string {
  throw new Error("not implemented");
}

/** Local wall-clock time with offset for a UTC instant. */
export function toLocalIso(instant: string, rules: ZoneRules): string {
  throw new Error("not implemented");
}
