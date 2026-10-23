export type Kind = "length" | "mass";

export interface LinearUnit {
  kind: Kind;
  /** How many base units (metres for lengths, grams for masses) make one of this unit. */
  factor: number;
}

export const LINEAR_UNITS: Record<string, LinearUnit> = {
  mm: { kind: "length", factor: 0.001 },
  cm: { kind: "length", factor: 0.01 },
  m: { kind: "length", factor: 1 },
  km: { kind: "length", factor: 1000 },
  in: { kind: "length", factor: 0.0254 },
  ft: { kind: "length", factor: 0.3048 },
  yd: { kind: "length", factor: 0.9144 },
  mi: { kind: "length", factor: 1609.344 },
  mg: { kind: "mass", factor: 0.001 },
  g: { kind: "mass", factor: 1 },
  kg: { kind: "mass", factor: 1000 },
  oz: { kind: "mass", factor: 28.349523125 },
  lb: { kind: "mass", factor: 453.59237 },
};

export const TEMPERATURE_UNITS = ["C", "F", "K"] as const;
