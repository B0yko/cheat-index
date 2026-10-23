# gatekeeper

Rule-based access checks for an internal admin tool. A policy is an ordered list of rules and a request says who
wants to do what to which resource.

```ts
type Rule = { effect: "allow" | "deny"; role: string; action: string; resource: string };
type Request = { roles: string[]; action: string; resource: string };
```

## When a rule matches a request

- **role**: the rule's `role` is one of the request's `roles`, or the rule's `role` is `"*"`.
- **action**: the rule's `action` equals the request's `action`, or is `"*"`.
- **resource**: the rule's `resource` equals the request's `resource`; or it is `"*"`, which matches every resource;
  or it ends in `/*`, which matches every resource that starts with the text before the `*` (`reports/*` matches
  `reports/2025/q1.csv` but not `reports` and not `reports-old/q1.csv`). A `*` anywhere else is an ordinary character.

A rule applies only when all three parts match.

## `isAllowed(rules, request): boolean`

1. If no rule matches, the request is denied (default deny).
2. If **any** matching rule is a `deny`, the request is denied. It does not matter where the deny rule is in the list or
   how specific the matching allow rules are: deny always wins.
3. Otherwise, at least one matching rule is an `allow`, and the request is allowed.

## `explain(rules, request): Decision`

Returns `{ allowed, rule }`. `allowed` is the same answer as `isAllowed`. `rule` is the rule that decided it: the first
matching `deny` rule when the request is denied by one, the first matching `allow` rule when it is allowed, and
`undefined` when it is denied by default.

## `allowedActions(rules, who, candidates): string[]`

`who` is `{ roles, resource }`. Returns those `candidates` for which `isAllowed` is true for that role set and
resource, in the order given.

## `matches(rule, request): boolean`

Whether one rule applies to a request, as described above.
