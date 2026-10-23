# rulecalc

Evaluates the small arithmetic formulas used in pricing rules, such as `base * (1 - rate) + 4`.

## `evaluate(formula, variables=None)`

`evaluate(formula: str, variables: Mapping[str, int | float] | None = None) -> int | float` returns the value of
the formula. `EvalError` (a subclass of `ValueError`) is raised for every problem.

### Language

- **Numbers** are decimal literals: digits with an optional fractional part (`42`, `0.25`). `.5`, `5.` and
  exponent notation are not numbers.
- **Variables** are names made of letters, digits and underscores that do not start with a digit. Their values come
  from the `variables` mapping.
- **Operators**, from loosest to tightest binding: `+ -`, then `* / %`, then `^` (power). Parentheses group.
- `+ - * / %` group left to right. `^` groups right to left: `2 ^ 3 ^ 2` is `2 ^ (3 ^ 2)`, which is `512`.
- Unary `-` and `+` bind tighter than `* / %` but looser than `^`: `-2 ^ 2` is `-4`, `2 * -3` is `-6`, and
  `2 ^ -2` is `0.25` (an exponent may carry a sign). Signs can be stacked: `--4` is `4`.
- **Functions**: `min(a, b, ...)` and `max(a, b, ...)` take one or more arguments, `abs(x)` takes exactly one. A
  name followed by `(` (spaces in between do not matter) is a function call, any other name is a variable, so
  `min + 1` reads the variable `min`.
- Whitespace between tokens is ignored.

`evaluate("2 + 3 * 4")` is `14`, and `evaluate("base * (1 - rate)", {"base": 80, "rate": 0.5})` is `40.0`.

### Values

Arithmetic on integers gives integers, so `2 ^ 70` is exactly `1180591620717411303424`. `/` always gives a float
(`7 / 2` is `3.5`). `%` is the remainder as Python's `%` computes it.

### Errors

`EvalError` is raised when

- the formula is empty or blank, contains a character that is not part of the language, has unbalanced
  parentheses, or lacks an operand or operator (`2 +`, `2 3`, `()`, `max(1,)`, `2 ** 3`);
- a variable is not in `variables`, or a function is unknown or gets the wrong number of arguments (`abs(1, 2)`,
  `min()`);
- the result would divide by zero (`/`, `%`, or `0 ^ -1`), or a power has no real result (a negative base with a
  fractional exponent, such as `(-8) ^ 0.5`).
