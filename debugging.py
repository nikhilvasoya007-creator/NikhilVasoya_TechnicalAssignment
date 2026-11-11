"""Debugging exercise (Part 11) — order total calculation.

BUGGY version (given in the assignment):
    def calculate_order_total(items):
        total = 0
        for item in items:
            total = item["qty"] * item["rate"]   # BUG: = overwrites, does not add
        return total

For items = [{"qty": 2, "rate": 100}, {"qty": 3, "rate": 50}]
buggy returns 150 (only the last item: 3 * 50)
correct returns 350 (2*100 + 3*50)
"""
from decimal import Decimal


def calculate_order_total(items):
    """Return the total amount for a list of {qty, rate} items.

    Rules:
    - Empty list -> 0.00 (no items, no total).
    - Missing qty or rate -> ValueError with a clear message.
    - qty must be a whole number > 0; rate must be a number >= 0.
    - Uses Decimal so money is exact to 2 places.
    """
    total = Decimal("0")
    for item in items:
        if "qty" not in item or "rate" not in item:
            raise ValueError("Each item must have 'qty' and 'rate'.")
        try:
            qty = int(item["qty"])
            rate = Decimal(str(item["rate"]))
        except (ValueError, TypeError, ArithmeticError):
            raise ValueError("qty must be a whole number and rate must be a number.")
        if qty <= 0:
            raise ValueError("qty must be greater than 0.")
        if rate < 0:
            raise ValueError("rate cannot be negative.")
        total += Decimal(qty) * rate
    return total.quantize(Decimal("0.01"))
