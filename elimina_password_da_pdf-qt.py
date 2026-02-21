# v1436

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QPlainTextEdit
from PyQt5.QtCore import Qt
import PyPDF2
import configparser
import os

class PDFPasswordRemover(QWidget):
    def __init__(self):
        super().__init__()
        self.config_file = 'config_pdf_free_password.ini'
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Rimuovi Password da PDF')

        layout = QVBoxLayout()

        self.label = QLabel('Inserisci la password del PDF:')
        layout.addWidget(self.label)

        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_entry)

        self.load_password()

        self.remove_button = QPushButton('Seleziona PDF e Rimuovi Password')
        self.remove_button.clicked.connect(self.remove_password)
        layout.addWidget(self.remove_button)

        self.drop_area = QPlainTextEdit('Trascina qui il PDF protetto da password')
        self.drop_area.setReadOnly(True)
        self.drop_area.setAcceptDrops(True)
        self.drop_area.setStyleSheet("background-color: lightgray;")
        layout.addWidget(self.drop_area)

        self.setLayout(layout)

    def load_password(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            if 'PDF' in config and 'password' in config['PDF']:
                self.password_entry.setText(config['PDF']['password'])

    def save_password(self, password):
        config = configparser.ConfigParser()
        config['PDF'] = {'password': password}
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)

    def remove_password(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleziona PDF", "", "PDF files (*.pdf)")
        
        if not file_path:
            return

        password = self.password_entry.text()
        if not password:
            QMessageBox.critical(self, "Errore", "Inserisci la password del PDF.")
            return

        self.save_password(password)

        self.process_pdf(file_path, password)

    def process_pdf(self, file_path, password):
        try:
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                if reader.is_encrypted:
                    reader.decrypt(password)
                    writer = PyPDF2.PdfWriter()
                    for page_num in range(len(reader.pages)):
                        writer.add_page(reader.pages[page_num])

                    if ".PDF" in file_path:
                        file_path = file_path.replace(".PDF", "_no_password.pdf")
                    elif ".pdf" in file_path:
                        file_path = file_path.replace(".pdf", "_no_password.pdf")
                            
                    output_path, _ = QFileDialog.getSaveFileName(self, "Salva PDF", file_path, "PDF files (*.pdf)")
                    if output_path:
                        with open(output_path, "wb") as output_file:
                            writer.write(output_file)
                        QMessageBox.information(self, "Successo", "La password è stata rimossa con successo.")
                else:
                    QMessageBox.information(self, "Informazione", "Il file PDF non è protetto da password.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Si è verificato un errore: {e}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.pdf') or file_path.endswith('.PDF'):
                password = self.password_entry.text()
                if not password:
                    QMessageBox.critical(self, "Errore", "Inserisci la password del PDF.")
                    return
                self.save_password(password)
                self.process_pdf(file_path, password)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PDFPasswordRemover()
    ex.show()
    sys.exit(app.exec_())