# v1436

import sys
import os
import configparser
from urllib.parse import unquote, urlparse
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QUrl
import PyPDF2

class Backend(QObject):
    # Segnali per comunicare con QML
    error = pyqtSignal(str, arguments=['msg'])
    info = pyqtSignal(str, arguments=['msg'])
    success = pyqtSignal(str, arguments=['msg'])
    saveDialogRequested = pyqtSignal(str, arguments=['suggestedUrl'])

    def __init__(self):
        super().__init__()
        self.config_file = 'config_pdf_free_password.ini'
        self.current_input_path = ""

    @pyqtSlot(result=str)
    def loadPassword(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            if 'PDF' in config and 'password' in config['PDF']:
                return config['PDF']['password']
        return ""

    @pyqtSlot(str)
    def savePassword(self, password):
        config = configparser.ConfigParser()
        config['PDF'] = {'password': password}
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)

    def _url_to_local_path(self, url_str):
        # QML fileUrl returns file:///...
        url = QUrl(url_str)
        if url.isLocalFile():
            return url.toLocalFile()
        # Fallback se è una stringa non formattata come QUrl valida
        parsed = urlparse(url_str)
        return unquote(parsed.path)

    @pyqtSlot(str, str)
    def requestPdfProcessing(self, file_url, password):
        self.savePassword(password)
        file_path = self._url_to_local_path(file_url)
        
        if not file_path:
            return

        try:
            self.current_input_path = file_path
            
            # Verifichiamo se è criptato
            reader = PyPDF2.PdfReader(file_path)
            if reader.is_encrypted:
                # Proviamo la decriptazione
                decrypted = reader.decrypt(password)
                if decrypted == 0:  # 0 indicates failed decryption
                    self.error.emit("Password errata o file non decifrato.")
                    return
                
                # Suggeriamo un nome file per il salvataggio
                suggested_path = file_path
                if ".PDF" in file_path:
                    suggested_path = file_path.replace(".PDF", "_no_password.pdf")
                elif ".pdf" in file_path:
                    suggested_path = file_path.replace(".pdf", "_no_password.pdf")
                
                # Trasformiamo in url per QML
                suggested_url = QUrl.fromLocalFile(suggested_path).toString()
                self.saveDialogRequested.emit(suggested_url)
            else:
                self.info.emit("Il file PDF non è protetto da password.")

        except Exception as e:
            self.error.emit(f"Si è verificato un errore in lettura: {e}")

    @pyqtSlot(str, str)
    def savePdf(self, output_url, password):
        output_path = self._url_to_local_path(output_url)
        if not output_path or not self.current_input_path:
            return

        try:
            with open(self.current_input_path, "rb") as input_file:
                reader = PyPDF2.PdfReader(input_file)
                reader.decrypt(password)
                writer = PyPDF2.PdfWriter()
                for page_num in range(len(reader.pages)):
                    writer.add_page(reader.pages[page_num])

                with open(output_path, "wb") as output_file:
                    writer.write(output_file)
            
            self.success.emit("La password è stata rimossa con successo.")
        except Exception as e:
            self.error.emit(f"Si è verificato un errore al salvataggio: {e}")

from PyQt5.QtCore import Qt

if __name__ == '__main__':
    # Necessario per i controlli QML, abilita anche il ridimensionamento High DPI
    QGuiApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    
    app = QGuiApplication(sys.argv)
    
    # Registriamo lo stile Material globalmente
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"
    
    engine = QQmlApplicationEngine()
    backend = Backend()
    
    # Esponiamo l'oggetto backend al contesto QML
    engine.rootContext().setContextProperty("backend", backend)
    
    # Carichiamo il file QML
    qml_file = os.path.join(os.path.dirname(__file__), 'main.qml')
    engine.load(QUrl.fromLocalFile(qml_file))
    
    if not engine.rootObjects():
        sys.exit(-1)
        
    sys.exit(app.exec_())