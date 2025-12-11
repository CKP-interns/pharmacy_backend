from __future__ import annotations

from django.db import transaction
from typing import Optional

from .models import SettingKV, DocCounter


def get_setting(key: str, default: str | None = None) -> str | None:
    row = SettingKV.objects.filter(pk=key).values_list("value", flat=True).first()
    if row is None:
        return default
    return row


@transaction.atomic
def set_setting(key: str, value: str) -> None:
    SettingKV.objects.update_or_create(key=key, defaults={"value": value})


@transaction.atomic
def next_doc_number(document_type: str, *args, prefix: str = "", padding: int | None = None) -> str:
    """Return and increment the next document number atomically.

    Backward-compatible signature: some callers may pass positional
    (prefix, padding). We accept those and map into keyword params.
    
    Automatically creates the DocCounter if it doesn't exist with sensible defaults.
    """
    # Back-compat: map optional positional args if provided
    if args:
        if len(args) >= 1 and not prefix:
            prefix = args[0]
        if len(args) >= 2 and padding is None:
            try:
                padding = int(args[1])
            except Exception:
                padding = None

    # Default prefixes for common document types
    default_prefixes = {
        "PO": "PO-",
        "GRN": "GRN-",
        "TRANSFER": "TR-",
        "INVOICE": "INV-",
    }
    
    # Default prefix and padding for the document type
    default_prefix = default_prefixes.get(document_type, f"{document_type}-")
    default_padding = 5  # Default padding for all counters
    
    # Use provided prefix or default for this document type
    default_prefix_value = prefix if prefix else default_prefix
    
    # Get or create the counter if it doesn't exist
    counter, created = DocCounter.objects.select_for_update().get_or_create(
        document_type=document_type,
        defaults={
            "prefix": default_prefix_value,
            "next_number": 1,
            "padding_int": padding if padding is not None else default_padding,
        }
    )
    
    # If counter was just created and we have a prefix argument, update it
    if created and prefix:
        counter.prefix = prefix
        counter.save(update_fields=["prefix"])
    
    num = counter.next_number
    eff_prefix = prefix if prefix != "" else counter.prefix
    eff_padding = padding if padding is not None else counter.padding_int
    code = f"{eff_prefix}{num:0{eff_padding}d}"
    counter.next_number = num + 1
    counter.save(update_fields=["next_number", "updated_at"])
    return code

