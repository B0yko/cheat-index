# portlist

Reads and tidies firewall port lists such as `25,80,8000-8100`.

## Port lists

A port list is a comma-separated list of items. An item is a port number (`443`) or a range `from-to`
(`8000-8100`). Ports are whole numbers from 1 to 65535, written with digits only. Spaces around an item and around
the `-` of a range are ignored. A list that is empty, or has only spaces, contains no ports.

## `parsePorts(list: string): Array<[number, number]>`

Returns the ports as ranges `[from, to]`, sorted by `from`. Ranges that overlap or touch (no port lies between
them) are merged: `10-20` and `21-30` become `10-30`, but `10-20` and `22-30` stay apart. A single port is
`[n, n]`.

## `normalizePorts(list: string): string`

The same list in canonical text form: the merged ranges in order, separated by `,` without spaces, a range of one
port written as just the number. `normalizePorts("80, 443,8080 - 8090,8091")` is `"80,443,8080-8091"`.

## `countPorts(list: string): number`

How many distinct ports the list contains.

## Errors

All three functions throw an `Error` for a malformed list: an empty item (`"80,,443"`, `"80,"`), anything that is
not a number, a port outside 1-65535, or a range whose end is below its start (`"90-80"`).
