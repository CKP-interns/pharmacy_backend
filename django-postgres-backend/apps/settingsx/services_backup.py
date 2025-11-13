from __future__ import annotations

from django.core.management import call_command
from django.db import transaction
from pathlib import Path
import io
import json

from .services import get_setting
from .models import BackupArchive
from apps.governance.services import audit


@transaction.atomic
def restore_backup(*, archive_id: int, actor) -> dict:
    if (get_setting("ALLOW_RESTORE", "false") or "false").lower() != "true":
        return {"ok": False, "code": "RESTORE_DISABLED"}
    if not getattr(actor, "is_superuser", False):
        return {"ok": False, "code": "FORBIDDEN"}

    arc = BackupArchive.objects.select_for_update().get(id=archive_id)
    file_url = arc.file_url
    p = Path(file_url)
    if not str(p).startswith("/media/backups/"):
        return {"ok": False, "code": "INVALID_PATH"}
    if not p.exists():
        return {"ok": False, "code": "NOT_FOUND"}

    call_command("loaddata", str(p))
    audit(actor, table="backup_archives", row_id=arc.id, action="RESTORE", before=None, after={"file": str(p)})
    return {"ok": True}


@transaction.atomic
def create_backup(*, actor) -> dict:
    base = Path("/media/backups")
    base.mkdir(parents=True, exist_ok=True)
    fname = base / ("backup.json")
    # Write dump
    with open(fname, "w", encoding="utf-8") as fh:
        call_command("dumpdata", "--natural-foreign", "--natural-primary", stdout=fh)
    size = fname.stat().st_size
    arc = BackupArchive.objects.create(file_url=str(fname), size_bytes=size, status=BackupArchive.Status.SUCCESS, created_by=actor if getattr(actor, "id", None) else None)
    audit(actor, table="backup_archives", row_id=arc.id, action="CREATE", after={"file": str(fname), "size": size})
    return {"ok": True, "archive_id": arc.id, "file_url": str(fname), "size_bytes": size}

