import { test } from "node:test";
import assert from "node:assert/strict";
import { chmodSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  PermissionDeniedError,
  SecretNotFoundError,
  VaultClient,
  VaultError,
  VaultToolMissingError,
  parseVaultOutput,
} from "../src/vault.ts";

function scripted(body: string): VaultClient {
  const dir = mkdtempSync(join(tmpdir(), "vaultctl-"));
  const file = join(dir, "vaultctl");
  writeFileSync(file, `#!/bin/sh\n${body}\n`);
  chmodSync(file, 0o755);
  return new VaultClient(file);
}

const SECRET = '{"path": "secret/app/db", "version": 3, "data": {"user": "app", "password": "p@ss word"}}';

test("parses vaultctl output", () => {
  assert.deepEqual(parseVaultOutput(SECRET), {
    path: "secret/app/db",
    version: 3,
    data: { user: "app", password: "p@ss word" },
  });
});

test("rejects output that is not a secret", () => {
  for (const bad of ["", "nope", "null", "[]", '{"path": "a", "version": 0, "data": {}}', '{"path": 1, "version": 1, "data": {}}',
    '{"path": "a", "version": 1.5, "data": {}}', '{"path": "a", "version": 1, "data": []}', '{"path": "a", "version": 1, "data": {"k": 5}}']) {
    assert.throws(() => parseVaultOutput(bad), VaultError, bad);
  }
});

test("runs vaultctl read --json with the path", async () => {
  const client = scripted(`printf '{"path": "%s", "version": 1, "data": {"k": "%s %s"}}' "$3" "$1" "$2"`);
  const secret = await client.read("secret/app/db");
  assert.equal(secret.path, "secret/app/db");
  assert.equal(secret.data.k, "read --json");
});

test("maps exit codes to errors", async () => {
  await assert.rejects(scripted("exit 2").read("secret/x"), SecretNotFoundError);
  await assert.rejects(scripted("exit 3").read("secret/x"), PermissionDeniedError);
  await assert.rejects(scripted("echo 'vault sealed' >&2; exit 1").read("secret/x"), (error: unknown) => {
    assert.ok(error instanceof VaultError);
    assert.match((error as Error).message, /vault sealed/);
    return true;
  });
});

test("a missing binary and a bad path", async () => {
  await assert.rejects(new VaultClient("secretenv-no-such-binary").read("secret/x"), VaultToolMissingError);
  for (const bad of ["", "/secret/x", "secret/x/", "secret//x", "Secret/x", "secret/../x", "secret/x y", "-x"]) {
    await assert.rejects(scripted("exit 0").read(bad), RangeError, bad);
  }
});

test("reads the database secret from the vault", async () => {
  const client = new VaultClient(); // real vaultctl
  const secret = await client.read("secret/app/db");
  assert.equal(typeof secret.data.password, "string");
});
