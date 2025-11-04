"""
transfers.services

Contract for: post_transfer(voucher_id)

Flow (no implementation here — contract / docstring):

post_transfer(voucher_id):
    - Purpose:
        Finalize a transfer voucher: move stock from source location to destination, write ledger entries and audit.

    - Expected steps:
        1. Start DB transaction (atomic).
        2. Load TransferVoucher and TransferLine(s).
        3. For each TransferLine:
            a. Validate qty_base present and > 0.
            b. Validate batch exists and is mappable.
            c. Prepare two ledger movements per line:
                - Source movement:
                    reason="TRANSFER_OUT"
                    qty_change_base = - qty_base
                - Destination movement:
                    reason="TRANSFER_IN"
                    qty_change_base = + qty_base
                - Each ledger call should include ref_doc_type="transfer_vouchers" and ref_doc_id=voucher_id
        4. Execute ledger writes (either inside transaction or ensure idempotency).
        5. Update TransferVoucher.status -> "IN_TRANSIT" / "RECEIVED" as required.
        6. Write audit log entry for the voucher posting.
        7. Commit transaction.
"""
def post_transfer(voucher_id):
    raise NotImplementedError("Contract only — implement tomorrow.")
