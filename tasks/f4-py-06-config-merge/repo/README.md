# confmerge

Layered configuration for a small service: built-in defaults, then config files, then environment variables.

## `deep_merge(base, override) -> dict`

Returns a new dict. Neither argument is changed, and nothing nested in the result is shared with them.

1. Keys that only one side has are kept.
2. When both sides have a dict under the same key, those dicts are merged recursively.
3. In every other case the override value wins. Lists and scalars are replaced, never combined, and a dict replaces a
   non-dict value.
4. An override value of `UNSET` removes that key from the result, at any depth. If the key is not there, nothing
   happens, and `UNSET` never ends up in the result.

## `env_overrides(environ, prefix="APP_") -> dict`

Turns environment variables into a nested dict of overrides.

1. Only names that start with `prefix` are used. The rest of the name is lower-cased and split on `__` into a path:
   `APP_DB__HOST=db1` becomes `{"db": {"host": "db1"}}`.
2. Values are converted: `true` and `false` (any case) become booleans, an optional `-` followed by digits becomes an
   `int`, everything else stays a string.
3. An empty path segment (`APP_DB____HOST`, or the prefix alone) raises `ValueError`.
4. A name that sets a value while another name sets something below it (`APP_DB=x` together with `APP_DB__HOST=y`)
   raises `ValueError`, whichever of the two comes first in `environ`.

## `build_config(defaults, *layers, environ=None, prefix="APP_", required=()) -> dict`

Starts from `defaults`, merges every layer on top in the order given, and then, if `environ` is passed, the overrides
from `env_overrides(environ, prefix)`. The process environment is never read unless the caller passes it in.

`required` is a list of dotted paths such as `"db.host"`. If one of them is missing from the final config, `ValueError`
is raised. A setting whose value is `None` counts as present. The arguments are not changed.
