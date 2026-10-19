"""Pull plain text out of uploaded files, keeping headings and structure where possible.

Works on the file's bytes in memory; nothing is written to disk.
"""

import io
from pathlib import Path

import docx
import pdfplumber
from docx.table import Table

MAX_FILE_BYTES = 10 * 1024 * 1024
SUPPORTED_TYPES = ("docx", "pdf", "md", "txt")
# A text-based PDF has far more than this many characters; a scanned one has close to none.
MIN_TEXT_CHARS = 50


class ExtractionError(ValueError):
    """The file can't be used. The message tells the user what to do next."""


def extract_text(filename: str, data: bytes) -> tuple[str, str]:
    """Return (file_type, text) for an uploaded file, or raise ExtractionError."""
    file_type = Path(filename).suffix.lower().lstrip(".")
    if file_type not in SUPPORTED_TYPES:
        raise ExtractionError(
            f"'{filename}' is not a supported file type. Please upload a .docx, .pdf, .md or .txt file."
        )
    if len(data) == 0:
        raise ExtractionError(f"'{filename}' is empty. Please check you picked the right file.")
    if len(data) > MAX_FILE_BYTES:
        size_mb = len(data) / (1024 * 1024)
        raise ExtractionError(f"'{filename}' is {size_mb:.1f} MB. The limit is 10 MB; try removing large images.")

    if file_type == "docx":
        text = _docx_text(filename, data)
    elif file_type == "pdf":
        text = _pdf_text(filename, data)
    else:
        text = _plain_text(data)

    text = text.strip()
    if len(text) < MIN_TEXT_CHARS:
        if file_type == "pdf":
            raise ExtractionError(
                f"No readable text found in '{filename}'. It looks like a scanned PDF (an image of pages). "
                "Please upload the original Word file, or a PDF exported from Word."
            )
        raise ExtractionError(f"'{filename}' has almost no text in it. Please check you picked the right file.")
    return file_type, text


def _docx_text(filename: str, data: bytes) -> str:
    try:
        document = docx.Document(io.BytesIO(data))
    except Exception:
        raise ExtractionError(
            f"'{filename}' couldn't be opened as a Word document. It may be damaged, password-protected, "
            "or an old .doc file. Open it in Word and save it as .docx, then try again."
        )

    lines = []
    # Paragraphs and tables, in the order they appear in the document.
    for block in document.iter_inner_content():
        if isinstance(block, Table):
            lines.extend(_table_lines(block))
            lines.append("")
            continue
        text = block.text.strip()
        if not text:
            continue
        style = (block.style.name if block.style is not None else "").lower()
        if style == "title":
            lines.append(f"# {text}")
        elif style.startswith("heading"):
            # "Heading 2" becomes "## " so the AI can see the document's structure.
            level = style.removeprefix("heading").strip()
            hashes = "#" * (int(level) if level.isdigit() else 1)
            lines.append(f"\n{hashes} {text}")
        elif "list" in style:
            lines.append(f"- {text}")
        else:
            lines.append(text)
    return "\n".join(lines)


def _table_lines(table: Table) -> list[str]:
    lines = []
    for row in table.rows:
        cells = []
        for cell in row.cells:
            value = " ".join(cell.text.split())
            if not cells or value != cells[-1]:  # merged cells repeat; show them once
                cells.append(value)
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def _pdf_text(filename: str, data: bytes) -> str:
    try:
        pages = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for number, page in enumerate(pdf.pages, start=1):
                page_text = (page.extract_text() or "").strip()
                if page_text:
                    # Page markers help the AI say where it found something.
                    pages.append(f"[Page {number}]\n{page_text}")
        return "\n\n".join(pages)
    except Exception:
        raise ExtractionError(
            f"'{filename}' couldn't be read as a PDF. It may be damaged or password-protected. "
            "Try re-saving it, or upload the original Word file."
        )


def _plain_text(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")  # older Windows text files
