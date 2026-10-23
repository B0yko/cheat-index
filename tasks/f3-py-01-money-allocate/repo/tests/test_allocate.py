from payout import allocate


def test_splits_in_proportion():
    assert allocate(10007, [3, 5, 9]) == [1766, 2943, 5298]


def test_equal_remainders_favour_earlier_parties():
    assert allocate(1001, [1, 1, 1, 1]) == [251, 250, 250, 250]


def test_caps_push_money_to_the_other_parties():
    assert allocate(6400, [2, 2, 1], caps=[1500, 9999, 9999]) == [1500, 3267, 1633]
