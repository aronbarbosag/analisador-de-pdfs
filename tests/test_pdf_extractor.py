from backend.services.pdf_extractor import PDFExtractor


def test_pdf_extractor_simple_pdf(tmp_path):
    extractor = PDFExtractor("assets/sample.pdf")

    extractor.save_text(str(tmp_path / "output.txt"))

    print(extractor.extract_text())
    print(extractor.extract_pages())

    assert extractor.extract_pages() is not None
    assert len(extractor.extract_pages()) > 0


def test_pdf_extractor_pdf_with_images(tmp_path):
    extractor = PDFExtractor("assets/sample_2.pdf")

    extractor.save_text(str(tmp_path / "output_sample_2.txt"))

    print(extractor.extract_text())
    print(extractor.extract_pages())

    assert extractor.extract_pages() is not None
    assert len(extractor.extract_pages()) > 0
