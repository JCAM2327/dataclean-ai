"""Persistencia de datasets aislada por usuario."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


class DatasetStore:
    """Almacena cada dataset bajo data/users/{user_id}/datasets/{id}/."""

    def __init__(self, root: Path | str = "data") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _user_dir(self, user_id: str) -> Path:
        safe = "".join(c for c in user_id if c.isalnum() or c in "-_") or "anonymous"
        path = self.root / "users" / safe / "datasets"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def create(self, user_id: str, filename: str, df: pd.DataFrame, report: dict[str, Any]) -> dict[str, Any]:
        dataset_id = uuid.uuid4().hex[:12]
        folder = self._user_dir(user_id) / dataset_id
        folder.mkdir(parents=True, exist_ok=True)
        df.to_csv(folder / "original.csv", index=False)
        record = {
            "dataset_id": dataset_id,
            "user_id": user_id,
            "filename": filename,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "applied": False,
            "report": report,
            "summary": report.get("summary", {}),
        }
        (folder / "meta.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        return record

    def get(self, user_id: str, dataset_id: str) -> dict[str, Any] | None:
        folder = self._user_dir(user_id) / dataset_id
        meta = folder / "meta.json"
        if not meta.exists():
            return None
        return json.loads(meta.read_text(encoding="utf-8"))

    def update(self, user_id: str, dataset_id: str, record: dict[str, Any], cleaned: pd.DataFrame | None = None) -> None:
        folder = self._user_dir(user_id) / dataset_id
        if not folder.exists():
            raise FileNotFoundError(dataset_id)
        (folder / "meta.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        if cleaned is not None:
            cleaned.to_csv(folder / "cleaned.csv", index=False)
