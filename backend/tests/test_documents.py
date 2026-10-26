from app.config import PROJECT_ROOT
from app.models import Document, DocumentVersion
from tests.pdf_helper import make_pdf

SAMPLES = PROJECT_ROOT / "samples"


def upload(client, filename, data, **fields):
    form = {"document_type": "brd", "uploaded_by": "Jordan", **fields}
    return client.post("/api/documents", files={"file": (filename, data)}, data=form)


def test_upload_creates_document_version_and_runs_review(client):
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
    assert version["reviews"][0]["status"] == "complete"  # the background review has run (demo mode)
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


# ---------- Optional Excel workbook (Part B) ----------

WORKBOOK = ("mapping.xlsx", (SAMPLES / "frd_mapping_sample.xlsx").read_bytes())


def upload_frd(client, workbook=None):
    files = {"file": ("frd.md", b"# FRD\n" + b"Functional requirements for invoice matching. " * 10)}
    if workbook:
        files["workbook"] = workbook
    return client.post("/api/documents", files=files, data={"document_type": "frd", "uploaded_by": "Jordan"})


def test_upload_with_workbook_keeps_its_text(client, session, frd_excel_rule):
    body = upload_frd(client, WORKBOOK).json()
    assert body["workbook_filename"] == "mapping.xlsx"
    version = session.get(DocumentVersion, body["version_id"])
    assert "## Sheet: Field Mapping" in version.workbook_text
    [summary] = client.get(f"/api/documents/{body['document_id']}").json()["versions"]
    assert summary["workbook_filename"] == "mapping.xlsx"


def test_upload_without_workbook(client, session, frd_excel_rule):
    body = upload_frd(client).json()
    assert body["workbook_filename"] is None
    assert session.get(DocumentVersion, body["version_id"]).workbook_text is None


def test_workbook_rejected_when_type_has_no_excel_rules(client, session):
    response = upload_frd(client, WORKBOOK)
    assert response.status_code == 400
    assert "has no Excel rules (Part B)" in response.json()["detail"]
    assert session.query(Document).count() == 0


def test_unusable_workbook_is_rejected(client, frd_excel_rule):
    response = upload_frd(client, ("mapping.xls", b"x" * 100))
    assert response.status_code == 400
    assert "save it as .xlsx" in response.json()["detail"]


def test_revised_version_with_workbook(client, frd_excel_rule):
    first = upload_frd(client, WORKBOOK).json()
    url = f"/api/documents/{first['document_id']}/versions"
    revised = client.post(url, files={"file": ("frd_v2.md", b"# FRD v2\n" + b"Revised requirements. " * 10), "workbook": WORKBOOK})
    assert revised.status_code == 201
    assert revised.json()["workbook_filename"] == "mapping.xlsx"
    # a workbook isn't carried over: a version uploaded without one has none
    third = client.post(url, files={"file": ("frd_v3.md", b"# FRD v3\n" + b"Revised again. " * 10)}).json()
    assert third["workbook_filename"] is None
    bad = client.post(url, files={"file": ("frd_v4.md", b"# FRD v4\n" + b"Revised again. " * 10), "workbook": ("m.csv", b"a,b")})
    assert bad.status_code == 400
    assert "Please upload a .xlsx file" in bad.json()["detail"]
