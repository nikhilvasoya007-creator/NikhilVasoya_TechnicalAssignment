import pytest
from decimal import Decimal
from debugging import calculate_order_total


def test_assignment_example():
    items = [{"qty": 2, "rate": 100}, {"qty": 3, "rate": 50}]
    assert calculate_order_total(items) == Decimal("350.00")


def test_empty_list():
    assert calculate_order_total([]) == Decimal("0.00")


def test_single_item():
    items = [{"qty": 2, "rate": 1500}]
    assert calculate_order_total(items) == Decimal("3000.00")


def test_missing_qty_rejected():
    with pytest.raises(ValueError):
        calculate_order_total([{"rate": 100}])


def test_missing_rate_rejected():
    with pytest.raises(ValueError):
        calculate_order_total([{"qty": 2}])


def test_zero_qty_rejected():
    with pytest.raises(ValueError):
        calculate_order_total([{"qty": 0, "rate": 100}])


def test_negative_rate_rejected():
    with pytest.raises(ValueError):
        calculate_order_total([{"qty": 2, "rate": -50}])
