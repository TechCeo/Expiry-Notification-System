from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout


class AboutDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setFixedSize(500, 220)

        title = QLabel("Product Expiry Notification System")
        font = title.font()
        font.setPointSize(20)
        title.setFont(font)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(QLabel("v2.0 — modular architecture"))
        layout.addWidget(QLabel("Copyright Okay TechCeo"))
        layout.addWidget(buttons)
