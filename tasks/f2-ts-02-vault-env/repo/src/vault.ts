export type VaultSecret = { path: string; version: number; data: Record<string, string> };

export class VaultError extends Error {}
export class VaultToolMissingError extends VaultError {}
export class SecretNotFoundError extends VaultError {}
export class PermissionDeniedError extends VaultError {}

/** Validate the JSON that `vaultctl read --json` prints. */
export function parseVaultOutput(stdout: string): VaultSecret {
  throw new Error("not implemented");
}

export class VaultClient {
  readonly binary: string;

  constructor(binary = "vaultctl") {
    this.binary = binary;
  }

  /** Read one secret through the vaultctl command line tool. */
  async read(path: string): Promise<VaultSecret> {
    throw new Error("not implemented");
  }
}
