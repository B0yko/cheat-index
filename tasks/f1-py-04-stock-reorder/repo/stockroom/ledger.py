"""In-memory stock ledger. See README.md for the rules."""


class InsufficientStock(Exception):
    """Raised when a reservation asks for more units than are available."""


class Stockroom:
    def __init__(self) -> None:
        self._on_hand: dict[str, int] = {}
        self._reorder_points: dict[str, int] = {}
        self._reservations: dict[str, dict[str, int]] = {}  # order id -> sku -> units

    def receive(self, sku: str, qty: int) -> None:
        if qty <= 0:
            raise ValueError("quantity must be positive")
        self._on_hand[sku] = self._on_hand.get(sku, 0) + qty

    def on_hand(self, sku: str) -> int:
        return self._on_hand.get(sku, 0)

    def set_reorder_point(self, sku: str, qty: int) -> None:
        if qty < 0:
            raise ValueError("reorder point cannot be negative")
        self._reorder_points[sku] = qty

    def reserved(self, sku: str) -> int:
        """Units of `sku` set aside for orders."""
        raise NotImplementedError

    def available(self, sku: str) -> int:
        """Units of `sku` that are on hand and not reserved."""
        raise NotImplementedError

    def reserve(self, order_id: str, sku: str, qty: int) -> None:
        """Set `qty` units of `sku` aside for an order."""
        raise NotImplementedError

    def release(self, order_id: str) -> None:
        """Give back everything the order had reserved."""
        raise NotImplementedError

    def reorder_list(self) -> list[str]:
        """SKUs that need restocking, in alphabetical order."""
        raise NotImplementedError
