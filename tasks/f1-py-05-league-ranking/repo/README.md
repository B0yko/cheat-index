# scoreboard

Ranking for the office quiz league. Players are given as a mapping from name to points.

## `standings(points: Mapping[str, int]) -> list[Standing]`

Returns one `Standing(rank, name, points)` per player, best first.

- Players are ordered by points, highest first.
- Players with equal points share a rank and are listed alphabetically (ignoring case).
- Ranks use standard competition ranking ("1224"): after a tie, the ranks that were shared are skipped. Points of
  95, 90, 90 and 85 give the ranks 1, 2, 2 and 4.
- An empty mapping gives an empty list.

## `podium(points, places=3) -> list[Standing]`

Every standing whose rank is at most `places`, so a tie at the edge of the podium makes the list longer.

## `rank_of(points, name) -> int`

The rank of one player. An unknown name raises `KeyError`.

## `format_table(points) -> str`

A plain-text table, one line per standing, joined with newlines and no trailing newline. A rank that is shared
with another player is shown with a trailing `=`. Each line is the rank label left-aligned in 3 characters, a space, the
name left-aligned in 8 characters, a space and the points right-aligned in 3 characters:

```
1   mira      95
2=  jonas     90
2=  pavel     90
4   lena      85
```
