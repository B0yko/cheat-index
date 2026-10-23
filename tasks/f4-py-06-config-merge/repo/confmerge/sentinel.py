"""The marker that removes a key during a merge."""


class _Unset:
    def __repr__(self) -> str:
        return "UNSET"


UNSET = _Unset()
