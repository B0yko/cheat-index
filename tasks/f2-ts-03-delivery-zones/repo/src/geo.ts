export type LatLng = { lat: number; lng: number };

/** Great-circle distance in kilometres. */
export function haversineKm(a: LatLng, b: LatLng): number {
  throw new Error("not implemented");
}

/** Delivery zone "A" to "E" for a distance in kilometres. */
export function zoneFor(distanceKm: number): "A" | "B" | "C" | "D" | "E" {
  throw new Error("not implemented");
}
