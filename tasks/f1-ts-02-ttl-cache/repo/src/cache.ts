export interface CacheOptions {
  ttlMs: number;
  maxEntries?: number;
  now?: () => number;
}

interface Entry<V> {
  value: V;
  expiresAt: number;
}

/** A cache whose entries expire. See README.md for the rules. */
export class TtlCache<V> {
  readonly #ttlMs: number;
  readonly #maxEntries: number | undefined;
  readonly #now: () => number;
  readonly #entries = new Map<string, Entry<V>>();

  constructor(options: CacheOptions) {
    throw new Error("not implemented");
  }

  set(key: string, value: V, ttlMs?: number): void {
    throw new Error("not implemented");
  }

  get(key: string): V | undefined {
    throw new Error("not implemented");
  }

  has(key: string): boolean {
    throw new Error("not implemented");
  }

  delete(key: string): boolean {
    throw new Error("not implemented");
  }

  get size(): number {
    throw new Error("not implemented");
  }

  keys(): string[] {
    throw new Error("not implemented");
  }

  prune(): number {
    throw new Error("not implemented");
  }
}
