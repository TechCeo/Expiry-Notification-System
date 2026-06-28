from __future__ import annotations

from PyQt5.QtWidgets import QDialog, QMessageBox, QPushButton, QSpinBox, QVBoxLayout

from src.services.inventory_service import InventoryService


class DeleteDialog(QDialog):
    def __init__(self, inventory: InventoryService, parent=None) -> None:
        super().__init__(parent)
        self._inventory = inventory
        self.setWindowTitle("Delete Product")
        self.setFixedSize(300, 110)

        self.product_id_input = QSpinBox()
        self.product_id_input.setRange(1, 2_147_483_647)
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self._delete)

        layout = QVBoxLayout(self)
        layout.addWidget(self.product_id_input)
        layout.addWidget(delete_button)

    def _delete(self) -> None:
        product_id = self.product_id_input.value()
        confirmation = QMessageBox.question(
            self,
            "Confirm deletion",
            f"Delete product {product_id}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirmation != QMessageBox.Yes:
            return
        try:
            deleted = self._inventory.delete_product(product_id)
        except Exception:
            QMessageBox.critical(self, "Database error", "The product could not be deleted.")
            return
        if not deleted:
            QMessageBox.information(self, "Not found", "No product has that ID.")
            return
        QMessageBox.information(self, "Product deleted", "The product was deleted successfully.")
        self.accept()
