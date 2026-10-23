export type Sample = { t: number; v: number };

export class MetricsError extends Error {}

/** Turn the decoded metrics service answer into samples. */
export function parseSeries(body: unknown): Sample[] {
  throw new Error("not implemented");
}
