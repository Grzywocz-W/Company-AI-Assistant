import io
import pypdf

def extractFromPDF(file_content_bytes: bytes):
    pdfReader =pypdf.PdfReader(io.BytesIO(file_content_bytes))
    textInPdf =""

    for page in pdfReader.pages:
        textFromPage = page.extract_text()
        if textFromPage:#not null
            textInPdf += textFromPage

    return str(textInPdf)#zabezpieczenie
