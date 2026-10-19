from app.config import PROJECT_ROOT
from app.models import Document
from tests.pdf_helper import make_pdf

SAMPLES = PROJECT_ROOT / "samples"


def upload(client, filename, data, **fields):
    form = {"document_type": "brd", "uploaded_by": "Jordan", **fields}
    return client.post("/api/documents", files={"file": (filename, data)}, data=form)


def test_upload_creates_document_version_and_queued_review(client):
    response = upload(client, "brd_strong.docx", (SAMPLES / "brd_strong.docx").read_bytes(), project_name="AP Automation")
    assert response.status_code == 201
    body = response.json()
    assert body["version_number"] == 1
    assert body["review_status"] == "queued"
    assert body["file_type"] == "docx"
    assert body["extracted_characters"] > 1000
    assert "Accounts Payable" in body["extracted_text_preview"]

    detail = client.get(f"/api/documents/{body['document_id']}").json()
    assert detail["title"] == "brd_strong"  # defaults to the file name
    assert detail["project_name"] == "AP Automation"
    assert detail["document_type"] == "brd"
    [version] = detail["versions"]
    assert version["original_filename"] == "brd_strong.docx"
    assert version["reviews"][0]["status"] == "queued"
    assert version["reviews"][0]["rulebook_version"] == 1


def test_upload_uses_given_title(client):
    body = upload(client, "x.md", (SAMPLES / "brd_weak.md").read_bytes(), title="  Invoicing BRD  ").json()
    assert client.get(f"/api/documents/{body['document_id']}").json()["title"] == "Invoicing BRD"


def test_upload_rejects_unsupported_file(client):
    response = upload(client, "diagram.png", b"x" * 100)
    assert response.status_code == 400
    assert "Please upload a .docx, .pdf, .md or .txt file" in response.json()["detail"]


def test_upload_rejects_scanned_pdf(client):
    response = upload(client, "scan.pdf", make_pdf([]))
    assert response.status_code == 400
    assert "scanned PDF" in response.json()["detail"]


def test_upload_requires_a_name(client):
    response = upload(client, "a.md", (SAMPLES / "brd_weak.md").read_bytes(), uploaded_by="   ")
    assert response.status_code == 400
    assert response.json()["detail"] == "Please enter your name."


def test_upload_rejects_unknown_type(client):
    response = upload(client, "a.md", (SAMPLES / "brd_weak.md").read_bytes(), document_type="nope")
    assert response.status_code == 400
    assert "Unknown document type 'nope'" in response.json()["detail"]


def test_failed_upload_saves_nothing(client, session):
    upload(client, "diagram.png", b"x" * 100)
    assert session.query(Document).count() == 0


def test_unknown_document(client):
    response = client.get("/api/documents/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "No document with ID 999."
