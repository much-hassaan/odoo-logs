"""Utilities for accounting."""
from odoo import models


def unit_price_from_tax(tax_id: models.Model = None, net: float = None, gross: float = None) -> float:
    """Returns appropriate unit price based on whether tax_id is price included."""
    if not tax_id:
        return gross or net

    if not net and not gross:
        return 0

    if tax_id.price_include:
        return gross or net * (1 + tax_id.amount / 100)
    else:
        return net or gross / (1 + tax_id.amount / 100)
