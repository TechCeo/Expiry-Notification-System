from __future__ import annotations

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
)

from src.domain.product import ProductCategory
from src.services.inventory_service import InventoryService


class InsertDialog(QDialog):
    def __init__(self, inventory: InventoryService, parent=None) -> None:
        super().__init__(parent)
        self._inventory = inventory
        self.setWindowTitle("Add New Product")
        self.setMinimumWidth(360)

        self.name_input = QLineEdit()
        self.name_input.setMaxLength(120)

        self.category_input = QComboBox()
        for category in ProductCategory:
            self.category_input.addItem(category.value, category)

        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(0, 1_000_000)
        self.quantity_input.setValue(1)

        self.expiry_input = QDateEdit(QDate.currentDate())
        self.expiry_input.setCalendarPopup(True)
        self.expiry_input.setDisplayFormat("dd-MM-yyyy")

        self.remarks_input = QLineEdit()
        self.remarks_input.setMaxLength(500)

        register_button = QPushButton("Register")
        register_button.clicked.connect(self._add_product)

        layout = QFormLayout(self)
        layout.addRow("Product name", self.name_input)
        layout.addRow("Category", self.category_input)
        layout.addRow("Quantity", self.quantity_input)
        layout.addRow("Expiry date", self.expiry_input)
        layout.addRow("Remarks", self.remarks_input)
        layout.addRow(register_button)

    def _add_product(self) -> None:
        qt_date = self.expiry_input.date()
        try:
            self._inventory.add_product(
                name=self.name_input.text(),
                category=self.category_input.currentData(),
                quantity=self.quantity_input.value(),
                expiry_date=qt_date.toPyDate(),
                remarks=self.remarks_input.text(),
            )
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Invalid product", str(error))
            return
        except Exception:
            QMessageBox.critical(self, "Database error", "The product could not be saved.")
            return

        QMessageBox.information(self, "Product added", "The product was added successfully.")
        self.accept()
