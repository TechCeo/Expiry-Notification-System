from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class ProductCategory(str, Enum):
    BEVERAGE = "Beverage"
    SOFT_DRINK = "Soft-Drink"
    COSMETICS = "Cosmetics"
    DETERGENTS = "Detergents"
    FRUITS = "Fruits"
    WATER = "Water"
    ANTISEPTIC = "Antiseptic"
    ALCOHOLIC_DRINK = "Alcoholic-Drink"
    MEDICAL = "Medical"
    CHOCOLATE = "Chocolate"
    TOOTH_PASTE = "Tooth-Paste"
    TOILETRIES = "Toiletries"
    PASTRIES = "Pastries"


class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True, slots=True)
class ProductCreate:
    name: str
    category: ProductCategory
    quantity: int
    expiry_date: date
    remarks: str = ""

    def __post_init__(self) -> None:
        cleaned_name = self.name.strip()
        cleaned_remarks = self.remarks.strip()
        if not cleaned_name:
            raise ValueError("Product name is required.")
        if len(cleaned_name) > 120:
            raise ValueError("Product name must be 120 characters or fewer.")
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative.")
        if len(cleaned_remarks) > 500:
            raise ValueError("Remarks must be 500 characters or fewer.")
        object.__setattr__(self, "name", cleaned_name)
        object.__setattr__(self, "remarks", cleaned_remarks)


@dataclass(frozen=True, slots=True)
class Product:
    id: int
    name: str
    category: ProductCategory
    quantity: int
    expiry_date: date
    remarks: str
    status: ProductStatus
    created_at: datetime
    updated_at: datetime
