import { VaultError, type VaultClient } from "./vault.ts";

/** The environment variable name for one field of a secret. */
export function envName(path: string, field: string): string {
  throw new Error("not implemented");
}

/** Render variables as the lines of a dotenv file. */
export function renderEnvFile(vars: Record<string, string>): string {
  throw new Error("not implemented");
}

/** Read the secrets at `paths` and map their fields to environment variables. */
export async function loadEnv(client: Pick<VaultClient, "read">, paths: string[]): Promise<Record<string, string>> {
  throw new Error("not implemented");
}
