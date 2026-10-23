import pytest

from invoicing import LineItem, invoice_summary, line_net_cents, tax_cents


def test_line_net_without_discount():
    assert line_net_cents(LineItem("PEN-BLK", 1999, 3)) == 5997


def test_line_net_with_discount():
    assert line_net_cents(LineItem("MUG-12", 1250, 2, discount_percent=10)) == 2250


def test_discount_is_rounded_to_a_cent():
    # 995 * 85% = 845.75 cents
    assert line_net_cents(LineItem("CAP-S", 995, 1, discount_percent=15)) == 846


def test_tax_simple():
    assert tax_cents(2000, 800) == 160


def test_tax_on_half_cent():
    # 1050 * 5% = 52.5 cents
    assert tax_cents(1050, 500) == 52


def test_summary_adds_up_line_taxes():
    items = [LineItem("A", 333, 1), LineItem("B", 333, 1)]
    summary = invoice_summary(items, 1000)
    assert summary.net_cents == 666
    assert summary.tax_cents == 66
    assert summary.total_cents == 732


def test_empty_invoice():
    summary = invoice_summary([], 2100)
    assert (summary.net_cents, summary.tax_cents, summary.total_cents) == (0, 0, 0)


def test_negative_quantity_is_rejected():
    with pytest.raises(ValueError):
        line_net_cents(LineItem("A", 100, -1))
