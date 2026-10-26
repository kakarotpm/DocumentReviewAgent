"""Create samples/frd_mapping_sample.xlsx: a small, realistic FRD mapping workbook for testing Part B.

Run from the backend folder:  .\.venv\Scripts\python.exe scripts\make_sample_xlsx.py
"""

from pathlib import Path

import openpyxl
from openpyxl.styles import Font

OUT = Path(__file__).resolve().parents[2] / "samples" / "frd_mapping_sample.xlsx"

SHEETS = {
    "Read Me": [
        ["Workbook", "AP Invoice Automation - Data Mapping"],
        ["FRD reference", "AP Invoice Automation FRD v1.0"],
        ["Version", "1.0"],
        ["Owner", "Jordan Patel"],
        ["Last updated", "2026-10-20"],
        ["Sheets", "Source Systems; Field Mapping; Joins; Measures; Reconciliation"],
    ],
    "Source Systems": [
        ["Source ID", "System", "Object", "Owner", "Refresh", "Notes"],
        ["SRC-01", "SAP ECC", "RBKP (invoice header)", "Finance IT", "Daily 02:00", ""],
        ["SRC-02", "SAP ECC", "RSEG (invoice lines)", "Finance IT", "Daily 02:00", ""],
        ["SRC-03", "SAP ECC", "EKKO (PO header)", "Procurement IT", "Daily 02:00", ""],
        ["SRC-04", "Supplier Portal", "invoices_api", "Digital team", "Hourly", "JSON via REST"],
    ],
    "Field Mapping": [
        ["Map ID", "FR Ref", "Target Table", "Target Field", "Data Type", "Nullable", "Source ID", "Source Field", "Transformation", "Default"],
        ["MAP-001", "FR-031", "fact_invoice", "invoice_id", "VARCHAR(20)", "N", "SRC-01", "BELNR", "Concatenate BUKRS + BELNR + GJAHR", ""],
        ["MAP-002", "FR-031", "fact_invoice", "supplier_id", "VARCHAR(10)", "N", "SRC-01", "LIFNR", "Trim leading zeros", ""],
        ["MAP-003", "FR-031", "fact_invoice", "invoice_date", "DATE", "N", "SRC-01", "BLDAT", "YYYYMMDD to DATE", ""],
        ["MAP-004", "FR-032", "fact_invoice", "gross_amount", "DECIMAL(15,2)", "N", "SRC-01", "RMWWR", "Convert to GBP using daily rate", ""],
        ["MAP-005", "FR-032", "fact_invoice", "currency", "CHAR(3)", "N", "SRC-01", "WAERS", "None", "GBP"],
        ["MAP-006", "FR-033", "fact_invoice", "po_number", "VARCHAR(10)", "Y", "SRC-02", "EBELN", "None", ""],
        ["MAP-007", "FR-034", "fact_invoice", "match_status", "VARCHAR(12)", "N", "Derived", "", "MATCHED if PO, supplier and amount agree within £5; else EXCEPTION", "EXCEPTION"],
    ],
    "Joins": [
        ["Join ID", "Left", "Right", "Type", "Keys", "Grain after join"],
        ["J-01", "RBKP", "RSEG", "INNER", "BUKRS, BELNR, GJAHR", "One row per invoice line"],
        ["J-02", "RSEG", "EKKO", "LEFT", "EBELN", "One row per invoice line"],
    ],
    "Measures": [
        ["Measure", "Definition", "Formula", "Filter", "Owner"],
        ["Invoice cycle time (days)", "Business days from receipt to approval", "NETWORKDAYS(received_date, approved_date)", "Approved invoices only", "AP Team Lead"],
        ["Auto-match rate", "Share of invoices matched without manual work", "COUNT(match_status='MATCHED') / COUNT(*)", "Invoices with a PO", "AP Team Lead"],
    ],
    "Reconciliation": [
        ["Check", "Source count / total", "Target count / total", "Tolerance", "Action if failed"],
        ["Invoice count per day", "COUNT(RBKP)", "COUNT(fact_invoice)", "0", "Stop load; alert Finance IT"],
        ["Gross amount per day (GBP)", "SUM(RMWWR converted)", "SUM(gross_amount)", "£1", "Investigate before release"],
    ],
}


def main():
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    for name, rows in SHEETS.items():
        sheet = workbook.create_sheet(name)
        for row in rows:
            sheet.append(row)
        for cell in sheet[1]:
            cell.font = Font(bold=True)
    workbook.save(OUT)
    print(f"Created {OUT.name}")


if __name__ == "__main__":
    main()
