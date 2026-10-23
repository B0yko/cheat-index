# buildplan

Orders build targets so that everything is built after the things it needs.

Dependencies are a mapping from a target name to the names it needs, like
`{"app": ["lib", "util"], "lib": ["util"]}`. A name that only appears as a dependency is a target without
dependencies of its own. Dependencies may be any iterable (list, tuple, set), and a name listed more than once
counts once. The input is never modified.

## `build_order(deps) -> list[str]`

Returns every target exactly once, each one after all of its dependencies.

- When several targets are ready at the same time (all their dependencies are already placed), the one that sorts
  first by plain string comparison comes next, so the order is the same on every run.
- `build_order({})` is `[]`.

`build_order({"app": ["lib", "util"], "lib": ["util"]})` is `["util", "lib", "app"]`.

### Cycles

If targets depend on each other in a loop, `build_order` raises `CycleError`. Its `cycle` attribute is a list of
names that starts and ends with the same name, where each name needs the next one: `["a", "b", "c", "a"]` means `a`
needs `b`, `b` needs `c` and `c` needs `a`. A target that needs itself is reported as `["a", "a"]`.

When there are several loops, the reported one is found like this. Go through the target names in alphabetical
order. From each target that has not been finished yet (a target is finished once all of its dependencies have
been followed to the end), follow its dependencies (also in alphabetical order) as deep as they go. The first time the search reaches a name that is already on the path being followed, the cycle is
the part of the path from that name onwards, followed by the name again.

## `rebuild_set(deps, changed) -> list[str]`

Returns the targets that have to be rebuilt after the targets in `changed` changed: the changed targets
themselves plus every target that needs one of them, directly or through other targets. The result is in build
order, so for the example above `rebuild_set(deps, ["util"])` is `["util", "lib", "app"]`. Names in `changed` that
do not occur in `deps` are ignored. `rebuild_set` raises `CycleError` for cyclic dependencies, like `build_order`.
