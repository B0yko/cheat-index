export type Token =
  | { kind: "text"; text: string }
  | { kind: "value"; expr: string; raw: boolean }
  | { kind: "if"; path: string }
  | { kind: "else" }
  | { kind: "end" };

/** Split a template into text and tag tokens. See README.md. */
export function tokenize(template: string): Token[] {
  throw new Error("not implemented");
}
