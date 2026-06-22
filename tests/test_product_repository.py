import tempfile
import unittest
import sqlite3
from datetime import date
from pathlib import Path

from src.domain.product import ProductCategory, ProductCreate
from src.infrastructure.database import Database
from src.repositories.product_repository import ProductRepository


class ProductRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "test.db")
        self.database.initialize()
        self.repository = ProductRepository(self.database)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_get_list_and_delete(self) -> None:
        created = self.repository.create(
            ProductCreate(
                name="Orange Juice",
                category=ProductCategory.BEVERAGE,
                quantity=4,
                expiry_date=date(2026, 7, 1),
                remarks="Fridge A",
            )
        )

        self.assertEqual(created, self.repository.get(created.id))
        self.assertEqual([created], self.repository.list_all())
        self.assertTrue(self.repository.delete(created.id))
        self.assertIsNone(self.repository.get(created.id))

    def test_initialize_migrates_legacy_products_idempotently(self) -> None:
        legacy_path = Path(self.temp_dir.name) / "legacy.db"
        connection = sqlite3.connect(legacy_path)
        connection.execute(
            """
            CREATE TABLE students (
                roll INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                branch TEXT,
                sem INTEGER,
                mobile INTEGER,
                address TEXT
            )
            """
        )
        connection.execute(
            """
            INSERT INTO students (name, branch, sem, mobile, address)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Milk", "Beverage", 2, "30-06-2026", "Fridge"),
        )
        connection.commit()
        connection.close()

        database = Database(legacy_path)
        database.initialize()
        database.initialize()
        products = ProductRepository(database).list_all()

        self.assertEqual(1, len(products))
        self.assertEqual("Milk", products[0].name)
        self.assertEqual(date(2026, 6, 30), products[0].expiry_date)


if __name__ == "__main__":
    unittest.main()
