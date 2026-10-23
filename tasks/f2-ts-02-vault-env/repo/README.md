# secretenv

Read application secrets from the vault with the `vaultctl` command line tool and write them out as a dotenv file.

## vaultctl

```
vaultctl read --json secret/app/db
```

prints the secret as JSON on stdout:

```json
{"path": "secret/app/db", "version": 3, "data": {"user": "app", "password": "p@ss word"}}
```

Exit code `2` means the path does not exist, `3` means permission denied, any other non-zero code is a failure with the
message on stderr.

## `src/vault.ts`

- `parseVaultOutput(stdout)` returns `{ path, version, data }`. `path` must be a string, `version` an integer of at least 1
  and `data` a plain object whose values are all strings. Invalid JSON or any other shape throws `VaultError`.
- `new VaultClient(binary = "vaultctl")` and `await client.read(path)` run `<binary> read --json <path>` (using
  `execFile`, no shell) and return `parseVaultOutput` of the output. A `path` must be lowercase segments of letters, digits,
  `_` and `-` joined by single `/`, with no leading or trailing `/`; otherwise `RangeError` before anything is run.
- Failures: a binary that cannot be found throws `VaultToolMissingError`; exit code 2 throws `SecretNotFoundError`, exit code 3
  `PermissionDeniedError` and any other failure `VaultError` with the stderr text in the message. All four extend
  `VaultError`.

## `src/envfile.ts`

- `envName(path, field)` builds a variable name from the last segment of the path and the field name, joined by `_`,
  uppercased, with every run of characters other than letters and digits replaced by one `_`, and leading and trailing `_`
  removed: `envName("secret/app/db", "password")` is `DB_PASSWORD`, `envName("secret/app/api-keys", "signing key")` is
  `API_KEYS_SIGNING_KEY`. A name that starts with a digit gets a `_` prefix. An empty `field` throws `RangeError`.
- `renderEnvFile(vars)` returns one `NAME=value` line per variable, sorted by name in plain code-unit order (the default of
  `Array.prototype.sort`), each line ending in a newline (an empty
  object gives `""`). A name must match `[A-Z_][A-Z0-9_]*`, otherwise `RangeError`. A value made only of letters, digits and
  `_ @ % + = : , . / -` is written as is, an empty value as nothing after the `=`. Any other value is wrapped in double
  quotes with backslash, double quote, `$`, newline and carriage return escaped (`\\`, `\"`, `\$`, `\n`, `\r`).
- `loadEnv(client, paths)` reads the secrets one after another with `client.read` and returns an object that maps `envName(path,
  field)` to the field value for every field. Two fields, of one secret or of different secrets, that produce the same variable name throw `VaultError`.
