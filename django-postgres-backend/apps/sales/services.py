"""
sales.services

Contract for: post_invoice(invoice_id)

Flow (no implementation here — contract / docstring):

post_invoice(invoice_id):
    - Purpose:
        Post a draft/ready SalesInvoice into 'posted' / 'final' state, perform ledger writes,
        recalculate totals, update payment status, audit.

    - Expected steps (high level):
        1. Load SalesInvoice and its SalesLine(s).
        2. For each SalesLine:
            a. Validate that it uses base units:
               - line must have qty_base (numeric)
               - rate_per_base must be present
               - sold_uom must be one of ("BASE", "PACK") for traceability
            b. Ensure batch is sellable:
               - batch_lot.status == "ACTIVE"
               - batch_lot.expiry_date is in future (not expired)
               - batch is not blocked (status != "BLOCKED")
            c. Ensure stock available at (location, batch):
               - Call Dev A's stock reader:
                   stock_on_hand(location_id, batch_lot_id) -> returns available qty in base units
               - Require available >= qty_base
            d. Prepare ledger movement:
               - For each line call Dev A's ledger writer:
                   write_movement(..., reason="SALE", qty_change_base = - qty_base, ref_doc_type="sales_invoices", ref_doc_id=invoice_id, ...)
        3. After all lines validated and ledger writes prepared:
            - Apply ledger writes (preferably within DB transaction / or in sequence if ledger is external)
            - Recalculate invoice totals: gross_total, tax_total, net_total from line totals
            - Update payment status based on payments attached (SalesPayment)
            - Write audit log entry (actor, before/after snapshot, action="POST_INVOICE")
        4. Return success/result (e.g., posted invoice id / status)

    - Notes / cross-team contracts:
        - Use Dev A's stock reader: stock_on_hand(location_id, batch_lot_id) -> numeric (base units)
        - Use Dev A's ledger writer: write_movement(location_id, batch_lot_id, reason, qty_change_base, ref_doc_type, ref_doc_id, meta...)
        - All qty math must be in base units (qty_base). If sold_uom == "PACK" frontend must also provide qty_base.
        - Errors to raise: insufficient stock, batch not sellable, data missing (qty_base/rate_per_base), ledger failures.
"""
def post_invoice(invoice_id):
    raise NotImplementedError("Contract only — implement tomorrow.")
