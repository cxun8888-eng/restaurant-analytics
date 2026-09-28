"""Small persistent store for processed datasets.

Files in this directory are created only by the API after a successful data
cleaning run.  Keeping the DataFrame in its native pandas representation
preserves dates and numeric types without adding a database dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import pickle
import re
from typing import Any, Dict

import pandas as pd


DATASET_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


@dataclass
class Dataset:
    frame: pd.DataFrame
    quality: Dict[str, Any]
    filename: str
    created_at: datetime
    owner_id: int | None = None
    anomaly_reviews: Dict[str, str] = field(default_factory=dict)


@dataclass
class PendingUpload:
    """An upload waiting for the user to confirm field mappings.

    The raw bytes are kept outside the processed dataset store so the review
    step can be completed without asking the browser to upload the file again.
    Pending files are short-lived and are never exposed through a dataset API.
    """

    payload: bytes
    filename: str
    created_at: datetime
    owner_id: int
    columns: list[str]
    quality: Dict[str, Any]
    suggestion: Dict[str, Any]


class DatasetStore:
    """Memory cache backed by one private file per processed dataset."""

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self._cache: dict[str, Dataset] = {}

    def _path(self, dataset_id: str) -> Path | None:
        if not DATASET_ID_PATTERN.fullmatch(dataset_id):
            return None
        return self.directory / f"{dataset_id}.pkl"

    def get(self, dataset_id: str) -> Dataset | None:
        cached = self._cache.get(dataset_id)
        if cached is not None:
            return cached

        path = self._path(dataset_id)
        if path is None or not path.is_file():
            return None
        try:
            with path.open("rb") as handle:
                item = pickle.load(handle)
        except (OSError, pickle.PickleError, EOFError):
            return None
        if not isinstance(item, Dataset):
            return None
        self._cache[dataset_id] = item
        return item

    def save(self, dataset_id: str, item: Dataset) -> None:
        path = self._path(dataset_id)
        if path is None:
            raise ValueError("无效的数据集标识")
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        try:
            with temporary.open("wb") as handle:
                pickle.dump(item, handle, protocol=pickle.HIGHEST_PROTOCOL)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        self._cache[dataset_id] = item

    def delete(self, dataset_id: str) -> bool:
        """Remove a persisted dataset and its in-memory cache entry."""
        path = self._path(dataset_id)
        if path is None:
            return False
        self._cache.pop(dataset_id, None)
        try:
            path.unlink()
        except FileNotFoundError:
            return False
        return True

    def inventory(self) -> list[dict[str, Any]]:
        """Return metadata only, loading at most one persisted frame at a time."""
        if not self.directory.is_dir():
            return []
        records: list[dict[str, Any]] = []
        for path in self.directory.glob("*.pkl"):
            dataset_id = path.stem
            if not DATASET_ID_PATTERN.fullmatch(dataset_id):
                continue
            item = self._cache.get(dataset_id)
            if item is None:
                try:
                    with path.open("rb") as handle:
                        item = pickle.load(handle)
                except (OSError, pickle.PickleError, EOFError):
                    continue
            if not isinstance(item, Dataset):
                continue
            records.append(
                {
                    "id": dataset_id,
                    "owner_id": item.owner_id,
                    "filename": item.filename,
                    "created_at": item.created_at,
                    "row_count": int(len(item.frame)),
                    "size_bytes": int(path.stat().st_size),
                }
            )
        return records

    def delete_owned(self, owner_id: int) -> list[str]:
        deleted: list[str] = []
        for item in self.inventory():
            if item["owner_id"] == owner_id and self.delete(item["id"]):
                deleted.append(item["id"])
        return deleted


class PendingUploadStore:
    """File-backed store for short-lived, user-scoped upload inspections."""

    def __init__(self, directory: str | Path, ttl_seconds: int = 1800):
        self.directory = Path(directory)
        self.ttl_seconds = max(60, int(ttl_seconds))
        self._cache: dict[str, PendingUpload] = {}

    def _path(self, inspection_id: str) -> Path | None:
        if not DATASET_ID_PATTERN.fullmatch(inspection_id):
            return None
        return self.directory / f"{inspection_id}.pkl"

    def _expired(self, item: PendingUpload) -> bool:
        return (datetime.utcnow() - item.created_at).total_seconds() > self.ttl_seconds

    def purge_expired(self) -> int:
        """Best-effort cleanup; called on startup and before new inspections."""
        if not self.directory.is_dir():
            return 0
        deleted = 0
        for path in self.directory.glob("*.pkl"):
            inspection_id = path.stem
            item = self._cache.get(inspection_id)
            if item is None:
                try:
                    with path.open("rb") as handle:
                        item = pickle.load(handle)
                except (OSError, pickle.PickleError, EOFError):
                    continue
            if isinstance(item, PendingUpload) and self._expired(item):
                deleted += int(self.delete(inspection_id))
        return deleted

    def get(self, inspection_id: str) -> PendingUpload | None:
        cached = self._cache.get(inspection_id)
        if cached is not None:
            if self._expired(cached):
                self.delete(inspection_id)
                return None
            return cached

        path = self._path(inspection_id)
        if path is None or not path.is_file():
            return None
        try:
            with path.open("rb") as handle:
                item = pickle.load(handle)
        except (OSError, pickle.PickleError, EOFError):
            return None
        if not isinstance(item, PendingUpload):
            return None
        if self._expired(item):
            self.delete(inspection_id)
            return None
        self._cache[inspection_id] = item
        return item

    def save(self, inspection_id: str, item: PendingUpload) -> None:
        self.purge_expired()
        path = self._path(inspection_id)
        if path is None:
            raise ValueError("无效的检查标识")
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        try:
            with temporary.open("wb") as handle:
                pickle.dump(item, handle, protocol=pickle.HIGHEST_PROTOCOL)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        self._cache[inspection_id] = item

    def delete(self, inspection_id: str) -> bool:
        path = self._path(inspection_id)
        if path is None:
            return False
        self._cache.pop(inspection_id, None)
        try:
            path.unlink()
        except FileNotFoundError:
            return False
        return True

    def inventory(self) -> list[dict[str, Any]]:
        if not self.directory.is_dir():
            return []
        records: list[dict[str, Any]] = []
        for path in self.directory.glob("*.pkl"):
            inspection_id = path.stem
            if not DATASET_ID_PATTERN.fullmatch(inspection_id):
                continue
            item = self._cache.get(inspection_id)
            if item is None:
                try:
                    with path.open("rb") as handle:
                        item = pickle.load(handle)
                except (OSError, pickle.PickleError, EOFError):
                    continue
            if not isinstance(item, PendingUpload):
                continue
            records.append(
                {
                    "id": inspection_id,
                    "owner_id": item.owner_id,
                    "filename": item.filename,
                    "created_at": item.created_at,
                    "size_bytes": int(path.stat().st_size),
                    "expired": self._expired(item),
                }
            )
        return records

    def delete_owned(self, owner_id: int) -> list[str]:
        deleted: list[str] = []
        for item in self.inventory():
            if item["owner_id"] == owner_id and self.delete(item["id"]):
                deleted.append(item["id"])
        return deleted
