# Database backup and restore engine.

import os
import shutil
from datetime import datetime
from pathlib import Path

BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"
DB_PATH = Path(__file__).resolve().parent.parent / "memory.db"


class BackupService:
    @staticmethod
    def _ensure_dir():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def create_backup() -> str:
        BackupService._ensure_dir()
        stamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
        dest = BACKUP_DIR / f"backup_{stamp}.db"
        shutil.copy2(DB_PATH, dest)
        from database import log_audit
        from config import OWNER_ID
        log_audit(OWNER_ID, "create_backup", "system", dest.name)
        return str(dest)

    @staticmethod
    def list_backups() -> list[str]:
        BackupService._ensure_dir()
        files = sorted(BACKUP_DIR.glob("backup_*.db"), reverse=True)
        return [f.name for f in files]

    @staticmethod
    def restore_backup(filename: str) -> bool:
        BackupService._ensure_dir()
        src = BACKUP_DIR / filename
        if not src.is_file() or not filename.startswith("backup_"):
            return False
        shutil.copy2(src, DB_PATH)
        from database import log_audit
        from config import OWNER_ID
        log_audit(OWNER_ID, "restore_backup", "system", filename)
        return True
