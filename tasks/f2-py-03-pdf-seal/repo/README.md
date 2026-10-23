# pdfseal

Sign and verify PDF invoices from Python by driving the in-house `pdfsignctl` command line tool.

## pdfsignctl

```
pdfsignctl sign --key KEY_ID --in FILE.pdf [--reason TEXT] [--stamp]
pdfsignctl verify --in FILE.pdf
```

`sign` writes `FILE.signed.pdf` next to the input. Both commands print a report on stdout:

```
status: signed
signer: CN=finance-2026,O=Example Ltd
signed_at: 2026-03-02T09:30:11Z
digest: sha256:9f2c...
output: invoice.signed.pdf
```

Exit code `0` means success, `3` an unknown key, `4` an input that is not a PDF. Any other non-zero code is a failure.

## `pdfseal/report.py`

`parse_report(text) -> SignReport` turns the report into `SignReport(status, signer, signed_at, digest, output)`; the
last four are `""` when the tool did not print them.

- Lines look like `key: value`. The key is everything before the first `:` (compared case-insensitively), the value is
  the rest, stripped. Blank lines, lines without `:` and unknown keys are ignored.
- `status` is required and must be `signed`, `valid`, `invalid` or `expired`; otherwise `ReportError`.
- A `digest` must start with `sha256:` followed by one or more hexadecimal digits, otherwise `ReportError`.
- `SignReport.ok` is true for the statuses `signed` and `valid`.

## `pdfseal/tool.py`

- `build_sign_command(path, key_id, *, reason=None, stamp=False) -> list[str]` gives the argument list, starting with
  `"pdfsignctl"`, `"sign"`, `"--key"`, the key id, `"--in"` and the path as text. `--reason TEXT` follows when a reason
  is given, then `--stamp` when requested. `ValueError` for a key id that is not 3 to 40 characters of lowercase
  letters, digits and hyphens starting with a letter or digit, for a path that does not end in `.pdf`
  (case-insensitive), and for a reason that is blank or contains a line break.
- `run_tool(args, *, timeout=30.0) -> str` runs the command and returns its stdout. A command that does not exist
  raises `ToolNotFoundError`; exit code 3 raises `UnknownKeyError`, exit code 4 `NotAPdfError`, any other non-zero
  code `SignError` with the code and stderr in the message, and a timeout `SignError` whose message contains "timed out".
  All of them are subclasses of `SignError`.
- `sign_pdf(path, key_id, *, reason=None, stamp=False) -> SignReport` builds the command, runs it and parses the
  report. `verify_pdf(path) -> SignReport` checks the path the same way (`ValueError` unless it ends in `.pdf`) and then does
  the same for `pdfsignctl verify --in PATH`.
