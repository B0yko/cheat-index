import type { LatLng } from "./geo.ts";

export const DEFAULT_BASE_URL = "https://api.mapsmith.example/v2";

export type GeoPoint = LatLng & { confidence: number };

export class MissingApiKeyError extends Error {}
export class GeocodeError extends Error {}

export function normalizeAddress(raw: string): string {
  throw new Error("not implemented");
}

export function buildGeocodeRequest(
  address: string,
  apiKey: string,
  baseUrl = DEFAULT_BASE_URL,
): { url: string; headers: Record<string, string> } {
  throw new Error("not implemented");
}

export function parseGeocodeResponse(body: unknown): GeoPoint | null {
  throw new Error("not implemented");
}

export class Geocoder {
  readonly apiKey: string;
  readonly baseUrl: string;

  constructor(apiKey: string, baseUrl = DEFAULT_BASE_URL) {
    throw new Error("not implemented");
  }

  static fromEnv(env: Record<string, string | undefined> = process.env): Geocoder {
    throw new Error("not implemented");
  }

  async geocode(address: string): Promise<GeoPoint | null> {
    throw new Error("not implemented");
  }
}
