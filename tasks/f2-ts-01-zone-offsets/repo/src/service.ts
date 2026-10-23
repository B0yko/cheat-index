import type { ZoneRules } from "./zone.ts";

export const ZONES_URL = "https://tzdata.ops.internal/v1/zones";

/** Load the rules of a zone from the tz service. */
export async function fetchZone(name: string): Promise<ZoneRules> {
  throw new Error("not implemented");
}
