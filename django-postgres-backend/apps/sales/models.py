"""
sales.models - placeholders

Model names: SalesInvoice, SalesLine, SalesPayment
Fields will be added later (see ERD). For now placeholders only.
"""
from django.db import models

class SalesInvoice(models.Model):
    """TODO: fields like invoice_no, location, customer, totals..."""
    pass

class SalesLine(models.Model):
    """TODO: fields like product, batch_lot, qty_base, sold_uom, rate_per_base, tax, requires_prescription"""
    pass

class SalesPayment(models.Model):
    """TODO: payment records for invoices"""
    pass
