from pathlib import Path

import pymupdf


class PDFExtractor:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def extract_text(self) -> str:
        with pymupdf.open(self.file_path) as doc:
            pages_text = [str(page.get_text()) for page in doc]
            text = "\n\n".join(pages_text)

        return text

    def extract_pages(self) -> list[dict]:
        pages = []

        with pymupdf.open(self.file_path) as doc:
            for page_number, page in enumerate(list(doc), start=1):  # type: ignore
                text = page.get_text()

                if text.strip():
                    pages.append({"page": page_number, "text": text})

        return pages

    def save_text(self, output_path: str = "output.txt") -> None:
        text = self.extract_text()
        Path(output_path).write_text(text, encoding="utf-8")
