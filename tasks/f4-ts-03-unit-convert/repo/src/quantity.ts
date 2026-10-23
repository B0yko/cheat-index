export interface Quantity {
  value: number;
  unit: string;
}

/** Read text such as "12.5 kg" into a number and a unit symbol. See README.md. */
export function parseQuantity(text: string): Quantity {
  throw new Error("not implemented");
}

/** Convert a quantity written as text, e.g. convertText("5 km", "mi") is "3.11 mi". */
export function convertText(text: string, to: string, digits = 2): string {
  throw new Error("not implemented");
}
