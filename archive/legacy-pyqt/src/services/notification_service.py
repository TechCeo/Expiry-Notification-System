from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Protocol

from plyer import notification

from src.domain.expiry_policy import ExpiryPolicy
from src.domain.product import Product
from src.repositories.product_repository import ProductRepository

LOGGER = logging.getLogger(__name__)


class Notifier(Protocol):
    def send(self, product: Product) -> None: ...


class PlyerNotifier:
    def send(self, product: Product) -> None:
        notification.notify(
            title="Product Expiry Alert",
            message=f"{product.name} expires on {product.expiry_date:%d-%m-%Y}",
            timeout=15,
        )


class ExpiryNotificationService:
    def __init__(
        self,
        repository: ProductRepository,
        notifier: Notifier,
        policy: ExpiryPolicy | None = None,
    ) -> None:
        self._repository = repository
        self._notifier = notifier
        self._policy = policy or ExpiryPolicy()

    def notify_expiring_products(self, today: date | None = None) -> int:
        reference_date = today or date.today()
        end_date = reference_date + timedelta(days=self._policy.warning_window_days)
        products = self._repository.list_expiring_between(reference_date, end_date)
        sent = 0
        for product in products:
            if self._policy.is_near_expiry(product, reference_date):
                self._notifier.send(product)
                sent += 1
        LOGGER.info("Expiry scan completed", extra={"notifications_sent": sent})
        return sent
