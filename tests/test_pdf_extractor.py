from backend.services.pdf_extractor import PDFExtractor


def test_pdf_extractor():
    extractor = PDFExtractor("assets/sample.pdf")

    extractor.save_text("output.txt")

    print(extractor.extract_text())
    print(extractor.extract_pages())

    assert extractor.extract_pages() is not None
    assert len(extractor.extract_pages()) > 0
