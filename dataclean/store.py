"""Persistencia de datasets aislada por usuario."""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from dataclean.io import load_dataframe


class DatasetStore:
    """Almacena cada dataset bajo data/users/{user_id}/datasets/{id}/."""

    ORIGINAL_STEM = "original"
    SNAPSHOT_FILENAME = "data.parquet"

    def __init__(self, root: Path | str = "data") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _user_dir(self, user_id: str) -> Path:
        safe = "".join(c for c in user_id if c.isalnum() or c in "-_") or "anonymous"
        path = self.root / "users" / safe / "datasets"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def dataset_dir(self, user_id: str, dataset_id: str) -> Path:
        return self._user_dir(user_id) / dataset_id

    def create(
        self,
        user_id: str,
        filename: str,
        df: pd.DataFrame,
        report: dict[str, Any],
        content: bytes | None = None,
    ) -> dict[str, Any]:
        dataset_id = uuid.uuid4().hex[:12]
        folder = self.dataset_dir(user_id, dataset_id)
        folder.mkdir(parents=True, exist_ok=True)

        if content is not None:
            ext = Path(filename).suffix.lower() or ".csv"
            original_name = f"{self.ORIGINAL_STEM}{ext}"
            (folder / original_name).write_bytes(content)
        else:
            original_name = f"{self.ORIGINAL_STEM}.csv"
            df.to_csv(folder / original_name, index=False)

        snapshot_name: str | None = None
        try:
            snapshot_path = folder / self.SNAPSHOT_FILENAME
            df.to_parquet(snapshot_path, index=False)
            if snapshot_path.exists() and snapshot_path.stat().st_size > 0:
                snapshot_name = self.SNAPSHOT_FILENAME
            else:
                snapshot_path.unlink(missing_ok=True)
        except Exception:
            snapshot_name = None

        record = {
            "dataset_id": dataset_id,
            "user_id": user_id,
            "filename": filename,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "applied": False,
            "original_file": original_name,
            "snapshot_file": snapshot_name,
            "report": report,
            "summary": report.get("summary", {}),
        }
        (folder / "meta.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        return record

    def get(self, user_id: str, dataset_id: str) -> dict[str, Any] | None:
        folder = self.dataset_dir(user_id, dataset_id)
        meta = folder / "meta.json"
        if not meta.exists():
            return None
        return json.loads(meta.read_text(encoding="utf-8"))

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        folder = self._user_dir(user_id)
        records: list[dict[str, Any]] = []
        for dataset_folder in folder.iterdir():
            if not dataset_folder.is_dir():
                continue
            meta = dataset_folder / "meta.json"
            if not meta.exists():
                continue
            try:
                records.append(json.loads(meta.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        records.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return records

    def delete(self, user_id: str, dataset_id: str) -> bool:
        folder = self.dataset_dir(user_id, dataset_id)
        if not folder.exists():
            return False
        shutil.rmtree(folder)
        return True

    def cleanup_expired(self, max_age_hours: float) -> int:
        if max_age_hours <= 0:
            return 0
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        users_root = self.root / "users"
        if not users_root.exists():
            return 0
        removed = 0
        for user_folder in users_root.iterdir():
            datasets_folder = user_folder / "datasets"
            if not datasets_folder.exists():
                continue
            for dataset_folder in datasets_folder.iterdir():
                meta = dataset_folder / "meta.json"
                if not meta.exists():
                    continue
                try:
                    record = json.loads(meta.read_text(encoding="utf-8"))
                    created = datetime.fromisoformat(record.get("created_at", ""))
                except (OSError, TypeError, AttributeError, ValueError, json.JSONDecodeError):
                    continue
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                if created < cutoff:
                    shutil.rmtree(dataset_folder, ignore_errors=True)
                    removed += 1
        return removed

    def load_original(self, user_id: str, dataset_id: str) -> pd.DataFrame:
        """Carga el dataset original preservando los tipos del frame analizado.

        Se prefiere el snapshot Parquet generado al subir el archivo para evitar
        que un round-trip por CSV altere tipos, ceros a la izquierda o fechas.
        """
        record = self.get(user_id, dataset_id)
        if record is None:
            raise FileNotFoundError(dataset_id)
        folder = self.dataset_dir(user_id, dataset_id)

        snapshot_name = record.get("snapshot_file") or self.SNAPSHOT_FILENAME
        snapshot_path = folder / snapshot_name
        if snapshot_path.exists() and snapshot_path.stat().st_size > 0:
            return pd.read_parquet(snapshot_path)

        original_name = record.get("original_file") or f"{self.ORIGINAL_STEM}.csv"
        original_path = folder / original_name
        if original_path.exists():
            return load_dataframe(original_path)

        legacy_path = folder / f"{self.ORIGINAL_STEM}.csv"
        if legacy_path.exists():
            return load_dataframe(legacy_path)
        raise FileNotFoundError(f"No se encontró el dataset original en {folder}")

    def update(self, user_id: str, dataset_id: str, record: dict[str, Any], cleaned: pd.DataFrame | None = None) -> None:
        folder = self.dataset_dir(user_id, dataset_id)
        if not folder.exists():
            raise FileNotFoundError(dataset_id)
        (folder / "meta.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        if cleaned is not None:
            cleaned.to_csv(folder / "cleaned.csv", index=False)
            try:
                parquet_path = folder / "cleaned.parquet"
                cleaned.to_parquet(parquet_path, index=False)
                if not parquet_path.exists() or parquet_path.stat().st_size == 0:
                    parquet_path.unlink(missing_ok=True)
            except Exception:
                pass
