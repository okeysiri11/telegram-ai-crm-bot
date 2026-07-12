# System validation for pre-migration hardening phase.

import os
from datetime import datetime


class PlatformHardeningTest:
    @staticmethod
    def run_validation() -> dict:
        from config import OWNER_ID
        from database import (
            cursor,
            conn,
            soft_delete,
            restore,
            attach_file,
            get_attachments,
            add_comment,
            get_comments,
            get_timeline,
            is_feature_enabled,
            assign_public_id,
        )

        steps = {}
        passed = 0
        total = 8

        def _check(name: str, ok: bool, detail: str = ""):
            nonlocal passed
            steps[name] = {"ok": ok, "detail": detail}
            if ok:
                passed += 1

        try:
            ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                INSERT INTO tasks (title, creator_id, status, deadline)
                VALUES (?, ?, 'NEW', ?)
                """,
                ("[HARDENING] soft delete test", OWNER_ID, ts),
            )
            conn.commit()
            tid = cursor.lastrowid

            deleted = soft_delete("task", tid, OWNER_ID)
            cursor.execute("SELECT is_deleted FROM tasks WHERE id = ?", (tid,))
            row = cursor.fetchone()
            _check("soft_delete", deleted and row and row[0] == 1, f"task={tid}")

            restored = restore("task", tid, OWNER_ID)
            cursor.execute("SELECT is_deleted FROM tasks WHERE id = ?", (tid,))
            row = cursor.fetchone()
            _check("restore", restored and row and row[0] == 0)

            cursor.execute(
                """
                INSERT INTO files (filename, original_filename, uploaded_by, module)
                VALUES ('test.bin', 'test.bin', ?, 'system')
                """,
                (OWNER_ID,),
            )
            conn.commit()
            fid = cursor.lastrowid
            aid = attach_file("TASK", tid, fid, OWNER_ID)
            atts = get_attachments("TASK", tid)
            _check("attachments", aid > 0 and len(atts) >= 1, f"attach={aid}")

            cid = add_comment("TASK", tid, OWNER_ID, "Hardening test comment")
            comments = get_comments("TASK", tid)
            _check("comments", cid > 0 and len(comments) >= 1, f"comment={cid}")

            tl = get_timeline("TASK", tid)
            _check("timeline", len(tl) >= 1, f"events={len(tl)}")

            ai_on = is_feature_enabled("ENABLE_AI_AGENTS")
            _check("feature_flags", ai_on is True)

            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "backup", "services/backup.py",
            )
            backup_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(backup_mod)
            BackupService = backup_mod.BackupService
            backup_path = BackupService.create_backup()
            backups = BackupService.list_backups()
            _check("backup", os.path.isfile(backup_path) and len(backups) >= 1, backup_path)

            pid = assign_public_id("tasks", tid)
            _check("public_ids", pid and pid.startswith("TK-"), pid or "")

            soft_delete("task", tid, OWNER_ID)

            pct = int(passed / total * 100)
            return {
                "ok": passed == total,
                "status": "SUCCESS" if passed == total else "PARTIAL",
                "passed": passed,
                "total": total,
                "migration_readiness_pct": pct,
                "steps": steps,
            }
        except Exception as exc:
            import traceback
            return {
                "ok": False,
                "status": "ERROR",
                "passed": passed,
                "total": total,
                "migration_readiness_pct": int(passed / total * 100) if total else 0,
                "steps": steps,
                "error": str(exc),
                "trace": traceback.format_exc(),
            }
