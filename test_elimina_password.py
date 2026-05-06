import os
import tempfile
import pytest
import PyPDF2
from PyQt5.QtCore import QUrl
from elimina_password_da_pdf import Backend

@pytest.fixture
def test_pdfs():
    """Crea PDF temporanei per i test."""
    temp_dir = tempfile.mkdtemp()
    
    unprotected_path = os.path.join(temp_dir, "unprotected.pdf")
    protected_path = os.path.join(temp_dir, "protected.pdf")
    
    # Crea PDF non protetto
    writer = PyPDF2.PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(unprotected_path, "wb") as f:
        writer.write(f)
        
    # Crea PDF protetto
    writer = PyPDF2.PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("testpass")
    with open(protected_path, "wb") as f:
        writer.write(f)
        
    yield unprotected_path, protected_path
    
    # Pulizia
    if os.path.exists(unprotected_path):
        os.remove(unprotected_path)
    if os.path.exists(protected_path):
        os.remove(protected_path)
    os.rmdir(temp_dir)

@pytest.fixture
def backend(qtbot):
    b = Backend()
    # Usiamo un file ini temporaneo
    temp_ini = tempfile.NamedTemporaryFile(delete=False, suffix='.ini')
    temp_ini.close()
    b.config_file = temp_ini.name
    yield b
    os.remove(temp_ini.name)

def test_url_to_local_path(backend):
    # Test valid QUrl format
    path = os.path.abspath("test.pdf").replace('\\', '/')
    url = QUrl.fromLocalFile(path).toString()
    result = backend._url_to_local_path(url).replace('\\', '/')
    assert result == path
    
def test_save_and_load_password(backend):
    assert backend.loadPassword() == ""
    backend.savePassword("mypass123")
    assert backend.loadPassword() == "mypass123"

def test_request_pdf_processing_unprotected(backend, qtbot, test_pdfs):
    unprotected_path, _ = test_pdfs
    url = QUrl.fromLocalFile(unprotected_path).toString()
    
    with qtbot.waitSignal(backend.info, timeout=1000) as blocker:
        backend.requestPdfProcessing(url, "anypass")
    
    assert "non è protetto da password" in blocker.args[0]

def test_request_pdf_processing_protected_wrong_password(backend, qtbot, test_pdfs):
    _, protected_path = test_pdfs
    url = QUrl.fromLocalFile(protected_path).toString()
    
    with qtbot.waitSignal(backend.error, timeout=1000) as blocker:
        backend.requestPdfProcessing(url, "wrongpass")
        
    assert "errata" in blocker.args[0]

def test_request_pdf_processing_protected_correct_password(backend, qtbot, test_pdfs):
    _, protected_path = test_pdfs
    url = QUrl.fromLocalFile(protected_path).toString()
    
    with qtbot.waitSignal(backend.saveDialogRequested, timeout=1000) as blocker:
        backend.requestPdfProcessing(url, "testpass")
        
    assert "_no_password.pdf" in blocker.args[0]

def test_save_pdf(backend, qtbot, test_pdfs):
    _, protected_path = test_pdfs
    
    # Prima prepariamo il backend processando il pdf corretto
    input_url = QUrl.fromLocalFile(protected_path).toString()
    backend.requestPdfProcessing(input_url, "testpass")
    
    # Definiamo dove salvare l'output
    output_path = protected_path.replace(".pdf", "_decrypted.pdf")
    output_url = QUrl.fromLocalFile(output_path).toString()
    
    with qtbot.waitSignal(backend.success, timeout=1000) as blocker:
        backend.savePdf(output_url, "testpass")
        
    assert "con successo" in blocker.args[0]
    
    # Verifichiamo che il nuovo file esista e sia leggibile senza password
    assert os.path.exists(output_path)
    reader = PyPDF2.PdfReader(output_path)
    assert not reader.is_encrypted
    
    os.remove(output_path)
