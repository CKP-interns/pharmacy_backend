"""
compliance.services - notes / contracts

Notes:
    - If any sales line has a controlled schedule (e.g., product.schedule in ["H","H1","NDPS","X"]), the invoice MUST have a linked Prescription.
    - On posting of sales lines that require H1/NDPS handling, create H1 / NDPS entries.
        * Creating H1/NDPS entries is scheduled for tomorrow's task (implementation detail).
    - Ensure all compliance checks and register creations are auditable (who, when).
"""
def ensure_prescription_for_invoice(invoice_id):
    raise NotImplementedError("Contract only — implement tomorrow.")
