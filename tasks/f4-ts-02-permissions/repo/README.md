# access-check

Role-based permission checks for an internal admin tool.

## Policy

A `Policy` maps a role name to a list of rules. A rule has an `effect` (`"allow"` or `"deny"`), a list of `actions`
and a list of `resources`; both lists hold patterns.

```ts
const policy: Policy = {
  editor: [
    { effect: "allow", actions: ["doc:*"], resources: ["docs/**"] },
    { effect: "deny", actions: ["doc:delete"], resources: ["docs/archive/**"] },
  ],
};
```

## `matchAction(pattern, action)`

Actions look like `doc:read` or `doc:comment:add`.

- `*` matches every action.
- A pattern that ends in `:*` matches every action that starts with the text before the `*` and has something after it:
  `doc:*` matches `doc:read` and `doc:comment:add`, but neither `docs:read`, `doc` nor `doc:`.
- Any other pattern must equal the action exactly (case matters). A `*` anywhere else has no special meaning.

## `matchResource(pattern, resource)`

Resources are slash-separated paths such as `projects/42/issues/7`. Empty segments, including leading and trailing
slashes, are ignored in both pattern and resource.

- Segments are compared one by one and must be equal (case matters).
- A `*` segment matches exactly one segment.
- A `**` segment matches any number of segments, including none: `projects/**` matches `projects` and
  `projects/42/issues/7`; `a/**/b` matches `a/b` and `a/x/y/b`.

## `isAllowed(policy, roles, action, resource)`

A request is allowed when at least one rule of at least one of the user's `roles` has effect `"allow"` and matches (any
of its action patterns matches the action and any of its resource patterns matches the resource), and no matching rule
with effect `"deny"` exists in any of those roles. Deny always wins. Roles that are not in the policy are ignored, and a
user without roles is denied.

## `allowedActions(policy, roles, actions, resource)`

The actions from `actions` that `isAllowed` accepts for that resource, in the order they were given.
