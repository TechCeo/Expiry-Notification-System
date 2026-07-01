from __future__ import annotations

from PyQt5.QtWidgets import QDialog, QMessageBox, QPushButton, QSpinBox, QVBoxLayout

from src.services.inventory_service import InventoryService


class SearchDialog(QDialog):
    def __init__(self, inventory: InventoryService, parent=None) -> None:
        super().__init__(parent)
        self._inventory = inventory
        self.setWindowTitle("Search Product")
        self.setFixedSize(300, 110)

        self.product_id_input = QSpinBox()
        self.product_id_input.setRange(1, 2_147_483_647)
        search_button = QPushButton("Search")
        search_button.clicked.connect(self._search)

        layout = QVBoxLayout(self)
        layout.addWidget(self.product_id_input)
        layout.addWidget(search_button)

    def _search(self) -> None:
        try:
            product = self._inventory.get_product(self.product_id_input.value())
        except Exception:
            QMessageBox.critical(self, "Database error", "The product could not be loaded.")
            return
        if product is None:
            QMessageBox.information(self, "Not found", "No product has that ID.")
            return
        details = (
            f"Product ID: {product.id}\n"
            f"Name: {product.name}\n"
            f"Category: {product.category.value}\n"
            f"Quantity: {product.quantity}\n"
            f"Expiry date: {product.expiry_date:%d-%m-%Y}\n"
            f"Remarks: {product.remarks}"
        )
        QMessageBox.information(self, "Product found", details)
