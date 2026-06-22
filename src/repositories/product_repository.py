from __future__ import annotations

from datetime import date, datetime
from sqlite3 import Row

from src.domain.product import Product, ProductCategory, ProductCreate, ProductStatus
from src.infrastructure.database import Database


class ProductRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def create(self, product: ProductCreate) -> Product:
        now = datetime.now().isoformat(timespec="seconds")
        with self._database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO products (
                    name, category, quantity, expiry_date, remarks,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
                """,
                (
                    product.name,
                    product.category.value,
                    product.quantity,
                    product.expiry_date.isoformat(),
                    product.remarks,
                    now,
                    now,
                ),
            )
            row = connection.execute(
                "SELECT * FROM products WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        if row is None:
            raise RuntimeError("Created product could not be loaded.")
        return self._to_product(row)

    def get(self, product_id: int) -> Product | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM products WHERE id = ?", (product_id,)
            ).fetchone()
        return self._to_product(row) if row else None

    def list_all(self) -> list[Product]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM products ORDER BY expiry_date, name"
            ).fetchall()
        return [self._to_product(row) for row in rows]

    def list_expiring_between(self, start: date, end: date) -> list[Product]:
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM products
                WHERE status = 'ACTIVE' AND expiry_date BETWEEN ? AND ?
                ORDER BY expiry_date, name
                """,
                (start.isoformat(), end.isoformat()),
            ).fetchall()
        return [self._to_product(row) for row in rows]

    def delete(self, product_id: int) -> bool:
        with self._database.connect() as connection:
            cursor = connection.execute("DELETE FROM products WHERE id = ?", (product_id,))
        return cursor.rowcount > 0

    @staticmethod
    def _to_product(row: Row) -> Product:
        try:
            category = ProductCategory(row["category"])
        except ValueError:
            category = ProductCategory.BEVERAGE
        return Product(
            id=row["id"],
            name=row["name"],
            category=category,
            quantity=row["quantity"],
            expiry_date=date.fromisoformat(row["expiry_date"]),
            remarks=row["remarks"],
            status=ProductStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
