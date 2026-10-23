import pytest

from stockroom import InsufficientStock, Stockroom


def make_room() -> Stockroom:
    room = Stockroom()
    room.receive("BOLT-M6-40", 100)
    room.receive("NUT-M6", 40)
    room.receive("CLAMP-25", 12)
    return room


def test_reserve_lowers_available_but_not_on_hand():
    room = make_room()
    room.reserve("SO-1001", "NUT-M6", 15)
    assert room.on_hand("NUT-M6") == 40
    assert room.reserved("NUT-M6") == 15
    assert room.available("NUT-M6") == 25


def test_reserving_more_than_available_changes_nothing():
    room = make_room()
    room.reserve("SO-1001", "CLAMP-25", 10)
    with pytest.raises(InsufficientStock):
        room.reserve("SO-1002", "CLAMP-25", 3)
    assert room.available("CLAMP-25") == 2


def test_one_order_can_reserve_a_sku_twice():
    room = make_room()
    room.reserve("SO-1001", "NUT-M6", 5)
    room.reserve("SO-1001", "NUT-M6", 7)
    assert room.reserved("NUT-M6") == 12


def test_release_gives_units_back():
    room = make_room()
    room.reserve("SO-1001", "NUT-M6", 5)
    room.reserve("SO-1001", "CLAMP-25", 2)
    room.release("SO-1001")
    assert room.available("NUT-M6") == 40
    assert room.available("CLAMP-25") == 12


def test_release_of_unknown_order_is_an_error():
    with pytest.raises(KeyError):
        make_room().release("SO-9999")


def test_sku_below_reorder_point_is_listed():
    room = make_room()
    room.set_reorder_point("CLAMP-25", 15)
    assert room.reorder_list() == ["CLAMP-25"]


def test_sku_above_reorder_point_is_not_listed():
    room = make_room()
    room.set_reorder_point("NUT-M6", 10)
    assert room.reorder_list() == []


def test_reservations_count_against_the_reorder_point():
    room = make_room()
    room.set_reorder_point("NUT-M6", 10)
    room.reserve("SO-1001", "NUT-M6", 35)
    assert room.reorder_list() == ["NUT-M6"]


def test_sku_at_reorder_point_is_not_listed():
    room = make_room()
    room.set_reorder_point("BOLT-M6-40", 100)
    assert room.reorder_list() == []


def test_reorder_list_is_alphabetical():
    room = make_room()
    room.set_reorder_point("NUT-M6", 50)
    room.set_reorder_point("CLAMP-25", 50)
    room.set_reorder_point("BOLT-M6-40", 500)
    assert room.reorder_list() == ["BOLT-M6-40", "CLAMP-25", "NUT-M6"]
