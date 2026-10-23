export type Query = Record<string, string | string[]>;

/** Parse a URL query string. See README.md for the rules. */
export function parseQuery(query: string): Query {
  throw new Error("not implemented");
}
