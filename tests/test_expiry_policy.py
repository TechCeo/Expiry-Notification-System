import unittest
from datetime import date, datetime, timedelta

from src.domain.expiry_policy import ExpiryPolicy
from src.domain.product import Product, ProductCategory, ProductStatus


def product(expiry_date: date, status: ProductStatus = ProductStatus.ACTIVE) -> Product:
    now = datetime(2026, 1, 1)
    return Product(
        id=1,
        name="Test product",
        category=ProductCategory.BEVERAGE,
        quantity=1,
        expiry_date=expiry_date,
        remarks="",
        status=status,
        created_at=now,
        updated_at=now,
    )


class ExpiryPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.today = date(2026, 1, 1)
        self.policy = ExpiryPolicy(warning_window_days=10)

    def test_includes_today_and_window_boundary(self) -> None:
        self.assertTrue(self.policy.is_near_expiry(product(self.today), self.today))
        self.assertTrue(
            self.policy.is_near_expiry(product(self.today + timedelta(days=10)), self.today)
        )

    def test_excludes_expired_future_and_archived_products(self) -> None:
        self.assertFalse(
            self.policy.is_near_expiry(product(self.today - timedelta(days=1)), self.today)
        )
        self.assertFalse(
            self.policy.is_near_expiry(product(self.today + timedelta(days=11)), self.today)
        )
        self.assertFalse(
            self.policy.is_near_expiry(
                product(self.today, ProductStatus.ARCHIVED), self.today
            )
        )


if __name__ == "__main__":
    unittest.main()
