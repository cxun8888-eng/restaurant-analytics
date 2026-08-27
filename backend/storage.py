"""Small persistent store for processed datasets.

Files in this directory are created only by the API after a successful data
cleaning run.  Keeping the DataFrame in its native pandas representation
preserves dates and numeric types without adding a database dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
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
