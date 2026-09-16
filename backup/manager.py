"""Backup and disaster recovery manager."""

import os
import json
import shutil
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
import hashlib


class BackupManager:
    """Manage backups and disaster recovery."""

    def __init__(self, backup_dir: str = "backups", db_path: str = "data/orchestrator.db"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path)
        self._retention_days = 30
        self._max_backups = 50

    async def create_backup(self, name: str = None) -> dict:
        """Create a full backup."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = name or f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)

        results = {
            "name": backup_name,
            "timestamp": timestamp,
            "files": [],
            "size_bytes": 0,
            "checksum": "",
        }

        # Backup database
        if self.db_path.exists():
            db_backup = backup_path / "orchestrator.db"
            shutil.copy2(self.db_path, db_backup)
            results["files"].append(str(db_backup))
            results["size_bytes"] += db_backup.stat().st_size

        # Backup .env file
        env_path = Path(".env")
        if env_path.exists():
            env_backup = backup_path / ".env"
            shutil.copy2(env_path, env_backup)
            results["files"].append(str(env_backup))

        # Backup configuration
        config_files = ["*.json", "*.yaml", "*.toml"]
        for pattern in config_files:
            for config_file in Path(".").glob(pattern):
                if config_file.name not in ["package-lock.json", "yarn.lock"]:
                    backup_file = backup_path / config_file.name
                    shutil.copy2(config_file, backup_file)
                    results["files"].append(str(backup_file))

        # Create manifest
        manifest = {
            "backup_name": backup_name,
            "timestamp": datetime.now().isoformat(),
            "files": results["files"],
            "total_size": results["size_bytes"],
        }

        manifest_path = backup_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        # Calculate checksum of manifest
        with open(manifest_path, "rb") as f:
            results["checksum"] = hashlib.sha256(f.read()).hexdigest()

        # Cleanup old backups
        await self._cleanup_old_backups()

        return results

    async def restore_backup(self, backup_name: str) -> dict:
        """Restore from a backup."""
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            return {"success": False, "error": f"Backup '{backup_name}' not found"}

        manifest_path = backup_path / "manifest.json"
        if not manifest_path.exists():
            return {"success": False, "error": "Invalid backup: missing manifest"}

        with open(manifest_path) as f:
            manifest = json.load(f)

        restored = []

        # Restore database
        db_file = backup_path / "orchestrator.db"
        if db_file.exists():
            # Create pre-restore backup
            await self.create_backup(f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(db_file, self.db_path)
            restored.append("database")

        # Restore .env
        env_file = backup_path / ".env"
        if env_file.exists():
            shutil.copy2(env_file, ".env")
            restored.append("env")

        return {
            "success": True,
            "restored": restored,
            "backup_name": backup_name,
            "backup_timestamp": manifest["timestamp"],
        }

    def list_backups(self) -> List[dict]:
        """List all available backups."""
        backups = []
        for backup_path in sorted(self.backup_dir.iterdir(), reverse=True):
            if backup_path.is_dir():
                manifest_path = backup_path / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path) as f:
                        manifest = json.load(f)
                    backups.append({
                        "name": manifest["backup_name"],
                        "timestamp": manifest["timestamp"],
                        "files": len(manifest["files"]),
                        "size": manifest["total_size"],
                    })
        return backups

    async def _cleanup_old_backups(self):
        """Remove backups older than retention period."""
        cutoff = datetime.now() - timedelta(days=self._retention_days)

        backups = sorted(self.backup_dir.iterdir(), key=lambda p: p.stat().st_mtime)

        # Keep at most max_backups
        if len(backups) > self._max_backups:
            for old_backup in backups[:len(backups) - self._max_backups]:
                shutil.rmtree(old_backup)

    async def verify_backup(self, backup_name: str) -> dict:
        """Verify backup integrity."""
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            return {"valid": False, "error": "Backup not found"}

        manifest_path = backup_path / "manifest.json"
        if not manifest_path.exists():
            return {"valid": False, "error": "Manifest missing"}

        with open(manifest_path) as f:
            content = f.read()
            manifest = json.loads(content)
            expected_checksum = hashlib.sha256(content.encode()).hexdigest()

        issues = []
        for file_path in manifest["files"]:
            if not Path(file_path).exists():
                issues.append(f"Missing: {file_path}")

        return {
            "valid": len(issues) == 0,
            "manifest_valid": True,
            "files_checked": len(manifest["files"]),
            "issues": issues,
        }

    def set_retention(self, days: int):
        """Set backup retention period."""
        self._retention_days = days

    def set_max_backups(self, count: int):
        """Set maximum number of backups to keep."""
        self._max_backups = count


# Global backup manager
backup_manager = BackupManager()
