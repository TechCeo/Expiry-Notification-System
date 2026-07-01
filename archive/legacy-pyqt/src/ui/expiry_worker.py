import logging

from PyQt5.QtCore import QThread, pyqtSignal

from src.services.notification_service import ExpiryNotificationService

LOGGER = logging.getLogger(__name__)


class ExpiryWorker(QThread):
    completed = pyqtSignal(int)
    failed = pyqtSignal(str)

    def __init__(self, notification_service: ExpiryNotificationService, parent=None) -> None:
        super().__init__(parent)
        self._notification_service = notification_service

    def run(self) -> None:
        try:
            sent = self._notification_service.notify_expiring_products()
            self.completed.emit(sent)
        except Exception as error:
            LOGGER.exception("Expiry notification scan failed")
            self.failed.emit(str(error))
