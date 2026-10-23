import type { Sample } from "./series.ts";

export const DEFAULT_BASE_URL = "https://metrics.ops.internal/v1";

export type MetricsClientOptions = { baseUrl?: string; fetchImpl?: typeof fetch };

export class MetricsClient {
  readonly baseUrl: string;
  readonly fetchImpl: typeof fetch;

  constructor(options: MetricsClientOptions = {}) {
    throw new Error("not implemented");
  }

  /** The samples of a metric over the last `windowSeconds` seconds. */
  async getSeries(metric: string, windowSeconds: number): Promise<Sample[]> {
    throw new Error("not implemented");
  }
}
