from __future__ import annotations

from pathlib import Path

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAction,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
)

from src.services.inventory_service import InventoryService
from src.services.notification_service import ExpiryNotificationService
from src.ui.dialogs import AboutDialog, DeleteDialog, InsertDialog, SearchDialog
from src.ui.expiry_worker import ExpiryWorker

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class MainWindow(QMainWindow):
    def __init__(
        self,
        inventory: InventoryService,
        notification_service: ExpiryNotificationService,
    ) -> None:
        super().__init__()
        self._inventory = inventory
        self._notification_service = notification_service
        self._expiry_worker: ExpiryWorker | None = None

        self.setWindowIcon(QIcon(str(PROJECT_ROOT / "icon" / "notification-icon-bell-alarm2.ico")))
        self.setWindowTitle("PRODUCT EXPIRY NOTIFICATION SYSTEM")
        self.setMinimumSize(800, 600)
        self._build_table()
        self._build_navigation()
        self.setStatusBar(QStatusBar(self))

    def _build_table(self) -> None:
        self.table = QTableWidget(self)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            (
                "Product ID",
                "Name",
                "Category",
                "Quantity",
                "Expiry Date",
                "Remarks",
                "Status",
                "Updated At",
            )
        )
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.setCentralWidget(self.table)

    def _build_navigation(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        help_menu = self.menuBar().addMenu("&About")
        toolbar = QToolBar(self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        actions = (
            ("Add New Product", "add-product.png", self.open_insert, file_menu),
            ("Refresh", "r3.png", self.load_data, None),
            ("Search Product", "s1.png", self.open_search, file_menu),
            ("Delete Product", "d1.png", self.open_delete, file_menu),
        )
        for label, icon_name, callback, menu in actions:
            action = QAction(QIcon(str(PROJECT_ROOT / "icon" / icon_name)), label, self)
            action.triggered.connect(callback)
            action.setStatusTip(label)
            toolbar.addAction(action)
            if menu is not None:
                menu.addAction(action)

        about_action = QAction(
            QIcon(str(PROJECT_ROOT / "icon" / "i1.png")), "Developer", self
        )
        about_action.triggered.connect(self.open_about)
        help_menu.addAction(about_action)

    def load_data(self) -> None:
        try:
            products = self._inventory.list_products()
        except Exception as error:
            QMessageBox.critical(self, "Database error", f"Products could not be loaded: {error}")
            return

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(products))
        for row_number, product in enumerate(products):
            values = (
                product.id,
                product.name,
                product.category.value,
                product.quantity,
                product.expiry_date.strftime("%d-%m-%Y"),
                product.remarks,
                product.status.value,
                product.updated_at.strftime("%Y-%m-%d %H:%M"),
            )
            for column_number, value in enumerate(values):
                self.table.setItem(row_number, column_number, QTableWidgetItem(str(value)))
        self.table.setSortingEnabled(True)
        self.statusBar().showMessage(f"Loaded {len(products)} products", 5000)

    def start_expiry_scan(self) -> None:
        if self._expiry_worker and self._expiry_worker.isRunning():
            return
        self._expiry_worker = ExpiryWorker(self._notification_service, self)
        self._expiry_worker.completed.connect(self._scan_completed)
        self._expiry_worker.failed.connect(self._scan_failed)
        self._expiry_worker.start()

    def _scan_completed(self, sent: int) -> None:
        self.statusBar().showMessage(f"Expiry scan complete: {sent} alert(s)", 5000)

    def _scan_failed(self, message: str) -> None:
        self.statusBar().showMessage(f"Expiry scan failed: {message}", 10000)

    def open_insert(self) -> None:
        dialog = InsertDialog(self._inventory, self)
        if dialog.exec_() == dialog.Accepted:
            self.load_data()

    def open_search(self) -> None:
        SearchDialog(self._inventory, self).exec_()

    def open_delete(self) -> None:
        dialog = DeleteDialog(self._inventory, self)
        if dialog.exec_() == dialog.Accepted:
            self.load_data()

    def open_about(self) -> None:
        AboutDialog(self).exec_()
