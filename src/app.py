from __future__ import annotations

import logging
import sys

from PyQt5.QtWidgets import QApplication

from src.infrastructure.database import Database
from src.repositories.product_repository import ProductRepository
from src.services.inventory_service import InventoryService
from src.services.notification_service import ExpiryNotificationService, PlyerNotifier
from src.ui.main_window import MainWindow


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def build_window() -> MainWindow:
    database = Database()
    database.initialize()
    repository = ProductRepository(database)
    inventory = InventoryService(repository)
    notification_service = ExpiryNotificationService(repository, PlyerNotifier())
    return MainWindow(inventory, notification_service)


def main() -> int:
    configure_logging()
    application = QApplication(sys.argv)
    window = build_window()
    window.show()
    window.load_data()
    window.start_expiry_scan()
    return application.exec_()
