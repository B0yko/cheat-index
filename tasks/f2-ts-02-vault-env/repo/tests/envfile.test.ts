import { test } from "node:test";
import assert from "node:assert/strict";
import { envName, loadEnv, renderEnvFile } from "../src/envfile.ts";
import { VaultError, type VaultSecret } from "../src/vault.ts";

test("builds variable names", () => {
  assert.equal(envName("secret/app/db", "password"), "DB_PASSWORD");
  assert.equal(envName("secret/app/api-keys", "signing key"), "API_KEYS_SIGNING_KEY");
  assert.equal(envName("secret/app/1st", "token"), "_1ST_TOKEN");
  assert.throws(() => envName("secret/app/db", ""), RangeError);
});

test("renders sorted lines and quotes only when needed", () => {
  const text = renderEnvFile({ B_URL: "https://x.test/a?b=1", A_PASSWORD: "p@ss word", C_EMPTY: "", D_PLAIN: "abc-1.2_3" });
  assert.equal(text, 'A_PASSWORD="p@ss word"\nB_URL="https://x.test/a?b=1"\nC_EMPTY=\nD_PLAIN=abc-1.2_3\n');
});

test("escapes quotes, dollars, backslashes and line breaks", () => {
  assert.equal(renderEnvFile({ K: 'a"b$c\\d\ne\rf' }), 'K="a\\"b\\$c\\\\d\\ne\\rf"\n');
});

test("rejects invalid names and renders nothing for nothing", () => {
  assert.equal(renderEnvFile({}), "");
  for (const bad of ["lower", "1ABC", "A-B", "A B", ""]) {
    assert.throws(() => renderEnvFile({ [bad]: "x" }), RangeError, bad);
  }
});

function fakeClient(secrets: Record<string, Record<string, string>>) {
  const calls: string[] = [];
  return {
    calls,
    async read(path: string): Promise<VaultSecret> {
      calls.push(path);
      if (!(path in secrets)) throw new VaultError(`unknown ${path}`);
      return { path, version: 1, data: secrets[path] };
    },
  };
}

test("loads fields of several secrets in order", async () => {
  const client = fakeClient({
    "secret/app/db": { user: "app", password: "pw" },
    "secret/app/mail": { "api key": "k-1" },
  });
  const env = await loadEnv(client, ["secret/app/db", "secret/app/mail"]);
  assert.deepEqual(env, { DB_USER: "app", DB_PASSWORD: "pw", MAIL_API_KEY: "k-1" });
  assert.deepEqual(client.calls, ["secret/app/db", "secret/app/mail"]);
});

test("conflicting variable names are an error", async () => {
  const client = fakeClient({ "secret/a/db": { user: "x" }, "secret/b/db": { user: "y" } });
  await assert.rejects(loadEnv(client, ["secret/a/db", "secret/b/db"]), VaultError);
});
