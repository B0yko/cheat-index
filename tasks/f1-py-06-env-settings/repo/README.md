# envconf

Typed readers for settings that arrive as environment variables. Every getter takes the environment as a mapping
(normally `os.environ`) and the name of the variable.

## Blank means unset

A variable that is missing, empty or made of whitespace only counts as **unset**, for every getter, and the getter
returns its default. Any other value is stripped of surrounding whitespace before it is interpreted.

## `get_str(env, key, default=None) -> str | None`

The stripped value, or `default` when the variable is unset.

## `get_bool(env, key, default=False) -> bool`

Reads a flag. `1`, `true`, `yes` and `on` give `True`; `0`, `false`, `no` and `off` give `False`; case does not matter.
Any other value raises `SettingError`. An unset variable gives `default`.

## `get_int(env, key, default=None, *, minimum=None, maximum=None) -> int | None`

Reads a base-10 integer; a leading `+` or `-` is allowed. A value that is not an integer raises `SettingError`, and so
does a value below `minimum` or above `maximum` (both limits are inclusive). An unset variable gives `default`, which
is returned as it is and is not checked against the limits.

## `get_list(env, key, default=()) -> list[str]`

Reads a comma-separated list. Items are stripped and empty items are dropped, so `"a, b,,c,"` gives
`["a", "b", "c"]`. An unset variable gives `list(default)`.

## Errors

`SettingError` is a subclass of `ValueError`; its message names the variable.
