from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Database:
    def __init__(self, path: str | Path | None = None) -> None:
        configured_path = path or os.getenv("EXPIRY_DB_PATH") or PROJECT_ROOT / "database.db"
        self.path = Path(configured_path).expanduser().resolve()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 120),
                    category TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK(quantity >= 0),
                    expiry_date TEXT NOT NULL,
                    remarks TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'ACTIVE'
                        CHECK(status IN ('ACTIVE', 'ARCHIVED')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_products_status_expiry
                ON products(status, expiry_date)
                """
            )
            self._migrate_legacy_products(connection)

    @staticmethod
    def _migrate_legacy_products(connection: sqlite3.Connection) -> None:
        legacy_table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'students'"
        ).fetchone()
        if legacy_table is None:
            return

        now = datetime.now().isoformat(timespec="seconds")
        migrated = 0
        for row in connection.execute(
            "SELECT roll, name, branch, sem, mobile, address FROM students"
        ):
            try:
                expiry_date = datetime.strptime(str(row["mobile"]), "%d-%m-%Y").date()
                quantity = max(0, int(row["sem"] or 0))
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO products (
                        id, name, category, quantity, expiry_date, remarks,
                        status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
                    """,
                    (
                        row["roll"],
                        str(row["name"] or "Unnamed product").strip(),
                        str(row["branch"] or "Beverage"),
                        quantity,
                        expiry_date.isoformat(),
                        str(row["address"] or "").strip(),
                        now,
                        now,
                    ),
                )
                migrated += cursor.rowcount
            except (TypeError, ValueError):
                LOGGER.warning("Skipped invalid legacy product", extra={"product_id": row["roll"]})
        if migrated:
            LOGGER.info("Migrated legacy products", extra={"product_count": migrated})
