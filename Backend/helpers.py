import io
import pypdf

def extractFromPDF(fileContentBytes: bytes):
    pdfReader = pypdf.PdfReader(io.BytesIO(fileContentBytes))
    textInPdf = ""

    for page in pdfReader.pages:
        textFromPage = page.extract_text()
        if textFromPage:#not null
            textInPdf += textFromPage

    return str(textInPdf)#zabezpieczenie

