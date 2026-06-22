from __future__ import annotations

from datetime import date

from src.domain.product import Product, ProductCategory, ProductCreate
from src.repositories.product_repository import ProductRepository


class InventoryService:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    def add_product(
        self,
        *,
        name: str,
        category: ProductCategory,
        quantity: int,
        expiry_date: date,
        remarks: str = "",
    ) -> Product:
        return self._repository.create(
            ProductCreate(
                name=name,
                category=category,
                quantity=quantity,
                expiry_date=expiry_date,
                remarks=remarks,
            )
        )

    def get_product(self, product_id: int) -> Product | None:
        if product_id <= 0:
            raise ValueError("Product ID must be greater than zero.")
        return self._repository.get(product_id)

    def list_products(self) -> list[Product]:
        return self._repository.list_all()

    def delete_product(self, product_id: int) -> bool:
        if product_id <= 0:
            raise ValueError("Product ID must be greater than zero.")
        return self._repository.delete(product_id)
