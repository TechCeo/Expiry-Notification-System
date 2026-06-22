from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .product import Product, ProductStatus


@dataclass(frozen=True, slots=True)
class ExpiryPolicy:
    """Select active products expiring inside an inclusive future window."""

    warning_window_days: int = 10

    def __post_init__(self) -> None:
        if self.warning_window_days < 0:
            raise ValueError("Warning window cannot be negative.")

    def is_near_expiry(self, product: Product, today: date | None = None) -> bool:
        reference_date = today or date.today()
        limit = reference_date + timedelta(days=self.warning_window_days)
        return (
            product.status is ProductStatus.ACTIVE
            and reference_date <= product.expiry_date <= limit
        )
