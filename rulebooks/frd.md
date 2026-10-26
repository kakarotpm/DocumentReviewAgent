---
doc_type: frd
display_name: Functional Requirements Document
pass_threshold: 80
description: Describes in detail what the system must do to meet the business requirements.
---

 Part A: Document rules

## FRD-01: Document control and sign-off
- weight: low
- critical: false
- check: The document has a title, version number, author, date and revision history,
  and a sign-off section naming the business and technical approvers (by name or role).
- pass_example: "v2.0, 02 Jun 2026, author: S. Rao. Approvers: Head of Finance Ops (business), IT Delivery Lead (technical)."
- fail_example: A revision history with no named approvers, or no version or date.

## FRD-02: Scope and source references
- weight: high
- critical: true
- check: The document states which solution, release or phase it covers, what is
  explicitly out of scope, and which source documents it is based on (e.g. the BRD,
  As-Is, To-Be) with their versions.
- pass_example: "Covers Phase 1 of invoice automation (India entities, PO invoices). Out of scope: payment runs, non-PO invoices. Based on BRD v1.2 and To-Be v1.0."
- fail_example: "This document describes the functional requirements of the new system." with no boundaries or source references.

## FRD-03: Traceability to business requirements
- weight: high
- critical: false
- check: Each functional requirement references the business requirement(s) it
  delivers, and every in-scope business requirement is covered by at least one
  functional requirement (via a column, reference or traceability matrix).
- pass_example: "FR-12 (auto-match within tolerance) → BR-07." Matrix shows all BRs covered.
- fail_example: Functional requirements with no link to the BRD; some business requirements have no matching functional requirement.

## FRD-04: User roles and permissions
- weight: high
- critical: false
- check: All user roles that interact with the system are listed, with what each
  role can view, create, edit, approve or delete. Every role named in the
  requirements appears in this list.
- pass_example: "AP Clerk: view/edit invoices, cannot approve. Approver: approve/reject invoices assigned to them. AP Admin: manage tolerance settings."
- fail_example: Requirements refer to "users" or "admin" with no definition of roles or what each can do.

## FRD-05: Functional requirements are stated and uniquely identified
- weight: high
- critical: true
- check: Functional requirements are listed individually, each with a unique ID,
  describing a specific behaviour of the system (what the system shall do), grouped
  by module, feature or process area.
- pass_example: "FR-12: The system shall automatically match an invoice to its PO and goods receipt when invoice number, PO number and supplier match."
- fail_example: Requirements written as paragraphs with no IDs, or restated business needs such as "The business needs faster invoice processing."

## FRD-06: Requirements are clear, atomic and testable
- weight: high
- critical: false
- check: Each requirement describes one behaviour, is unambiguous and can be tested.
  Vague terms such as "fast", "user-friendly", "easy", "flexible", "appropriate",
  "etc." or "and/or" are absent or quantified.
- pass_example: "FR-15: The system shall display the match result (Matched, Partial, Unmatched) on the invoice detail screen within 3 seconds of submission."
- fail_example: "FR-15: The system should match invoices quickly and show results in a user-friendly way, and handle exceptions etc."

## FRD-07: Acceptance criteria
- weight: high
- critical: true
- check: Each functional requirement (or user story) has acceptance criteria that
  define when it is met, covering the expected result and key negative or boundary
  cases, e.g. in Given/When/Then form.
- pass_example: "Given an invoice whose amount is within 2% of the PO, when it is submitted, then its status is set to Matched and it is routed for posting."
- fail_example: No acceptance criteria, or "Acceptance: works as expected."

## FRD-08: Functional flows or use cases
- weight: high
- critical: false
- check: The main user and system flows are described (as use cases, user stories
  with flows, or process flows), each with actors, preconditions, the main flow,
  alternate flows, exception flows and postconditions.
- pass_example: "UC-03 Approve invoice. Actor: Approver. Pre: invoice in Pending Approval. Main: open → review → approve. Alt: reject with reason. Exception: approver on leave → delegate."
- fail_example: Only a list of features with no description of how users move through them.

## FRD-09: Business rules, calculations and validations
- weight: high
- critical: false
- check: The rules the system must apply are stated explicitly: validations,
  conditions, thresholds, calculations, defaults and status transitions, with
  exact values rather than examples.
- pass_example: "BR-R4: Tolerance = lower of 2% of PO value or ₹10,000. Status flow: Received → Matched/Exception → Approved → Posted."
- fail_example: "The system validates invoices according to the applicable rules."

## FRD-10: Data requirements overview
- weight: low
- critical: false
- check: The document summarises the data the solution uses or produces (main data
  domains, source systems and outputs) and points to the embedded mapping workbook
  for field-level detail. Field-level mapping itself is evaluated in Part B.
- pass_example: "Data: invoice, PO, goods receipt and vendor data from SAP S/4HANA; outputs to AP dashboard. Field mapping: see embedded workbook 'AP_Data_Mapping', sheets 2–5."
- fail_example: No description of data or sources in the document, and no reference to where the mapping is held.

## FRD-11: Screens and user interface
- weight: medium
- critical: false
- check: The screens or interfaces users interact with are described, with the fields,
  actions and behaviour on each, and wireframes or mockups are included or referenced.
- pass_example: "Invoice detail screen: header fields, line items, match status badge, Approve/Reject buttons (Approver only). See wireframe W-04."
- fail_example: No description of screens, or "UI to be designed by the vendor" with no functional expectations.

## FRD-12: Integrations and interfaces
- weight: high
- critical: false
- check: Every external system the solution exchanges data with is listed, with the
  direction, data exchanged, trigger or frequency, and what happens if the exchange
  fails.
- pass_example: "SAP S/4HANA: outbound posted invoices (real time); inbound PO and GRN data (every 15 min). On failure: retry 3 times, then alert AP Admin."
- fail_example: "The system will integrate with SAP." with no data, direction, timing or failure handling.

## FRD-13: Reports, notifications and outputs
- weight: medium
- critical: false
- check: Reports, dashboards, notifications, emails and exports are specified with
  their content, recipients, trigger or schedule, and format.
- pass_example: "Daily 9 AM email to each Approver listing invoices pending > 2 days, with links. Monthly ageing report (Excel) for AP Lead."
- fail_example: "Users will receive notifications." with no trigger, recipient or content.

## FRD-14: Error handling and messages
- weight: medium
- critical: false
- check: The document states how the system behaves when inputs are invalid or
  operations fail, including the messages shown to users and whether actions are
  blocked, warned or logged.
- pass_example: "If GSTIN fails validation, block submission and show: 'GSTIN format is invalid. Check the 15-character number.'"
- fail_example: No mention of invalid inputs or failures beyond the happy path.

## FRD-15: Non-functional requirements
- weight: high
- critical: false
- check: Non-functional requirements are stated with measurable targets: performance,
  availability, capacity/volumes, scalability, usability, accessibility and
  supported devices or browsers, as relevant.
- pass_example: "Support 6,000 invoices/month and 50 concurrent users; search results in < 2 s; 99.5% availability during business hours."
- fail_example: "The system should be fast, reliable and scalable."

## FRD-16: Security, privacy and audit
- weight: medium
- critical: false
- check: The document states authentication, authorisation, data protection,
  privacy and audit trail requirements, including which actions are logged and how
  long records are retained.
- pass_example: "SSO via Azure AD. Bank details masked except for AP Admin. All approvals and edits logged with user and timestamp; logs retained 8 years."
- fail_example: No mention of access control, sensitive data or audit logging for a system handling financial data.

## FRD-17: Data migration
- weight: low
- critical: false
- check: If the solution replaces or loads data from an existing system or source,
  the document states what data is migrated, from where, any transformation or
  cleansing, and how it is validated; otherwise it states that no migration applies.
- pass_example: "Migrate open invoices (≈1,200) from the AP Excel tracker; reconcile counts and totals before go-live."
- fail_example: The solution replaces a tracker or legacy system, but migration is not mentioned.

## FRD-18: Assumptions, constraints and dependencies
- weight: medium
- critical: false
- check: Assumptions, constraints (technical, regulatory, budget, timeline) and
  dependencies on other systems, teams or projects that affect the functional design
  are listed explicitly.
- pass_example: "Constraint: must use existing SAP instance. Dependency: vendor master cleanup complete by Nov 2026. Assumption: suppliers send PDF invoices."
- fail_example: None listed, although the requirements rely on other systems and teams.

## FRD-19: Functional, not technical design
- weight: medium
- critical: false
- check: Requirements describe what the system must do from a user and business
  perspective. They do not prescribe internal design (database tables, code
  structure, specific frameworks) unless that is a stated constraint.
- pass_example: "FR-20: The system shall retain the original invoice PDF and link it to the invoice record."
- fail_example: "FR-20: Create a BLOB column in tbl_invoice and write a Spring Boot service to store the PDF."

## FRD-20: Open issues and decisions
- weight: low
- critical: false
- check: Unresolved questions and pending decisions are recorded with an owner and
  target date, rather than left as "TBD" inside requirements.
- pass_example: "OI-02: Approval delegation rules for leave – owner: Head of Finance Ops, due 15 Jul 2026."
- fail_example: Several requirements contain "TBD" with no owner or tracking.

## FRD-21: Completeness (no placeholders)
- weight: medium
- critical: false
- check: The document contains no unfinished sections: no empty tables or headings,
  "TBD" values, or missing wireframes or diagrams referenced in the text.
- pass_example: All sections populated; referenced wireframes W-01 to W-06 are attached.
- fail_example: An empty integration section and a reference to "wireframe W-04" that is not included.

## FRD-22: Internal consistency
- weight: medium
- critical: false
- check: Requirement IDs are unique and sequential, field names, roles, statuses and
  values are consistent across requirements, rules, data definitions and screens,
  and no requirements contradict each other.
- pass_example: The status "Pending Approval" is used identically in rules, screens and reports; tolerance is 2% everywhere.
- fail_example: Tolerance is 2% in FR-12 and 5% in the business rules; FR-18 appears twice with different text.

# Part B: Excel rules

## FRD-XL-01: Workbook structure
- weight: medium
- critical: false
- check: The workbook is organised into clearly named sheets by purpose (e.g. Sources,
  Data Mapping, Joins, Measures, Dimensions, Filters, Report Mapping), each with a
  single header row and one table per sheet. There are no merged header cells,
  unlabelled columns or hidden sheets holding live content.
- pass_example: Sheets "1_Sources", "2_Data_Mapping", "3_Joins", "4_Measures", "5_Report_Mapping", each starting with a header row in row 1.
- fail_example: One sheet mixing mapping, notes and measure formulas in separate blocks, with merged headers and a hidden sheet containing the latest joins.

## FRD-XL-02: Row identifiers and linkage to the document
- weight: medium
- critical: false
- check: Every mapping, join and measure row has a unique ID, and rows reference the
  functional requirement(s) in the Word document they support.
- pass_example: "MAP-014 | FR-21" and "MSR-03 | FR-24" in the ID and requirement columns.
- fail_example: Rows with no IDs, or IDs repeated across rows, and no way to tell which requirement a row belongs to.

## FRD-XL-03: Source identification
- weight: high
- critical: true
- check: Every source used is listed with its system, database or schema, table,
  view, file or API, the owner, access method and refresh availability.
- pass_example: "SRC-02 | SAP S/4HANA | schema SAPHANADB | table RBKP (invoice header) | owner: SAP CoE | via CDS view / BW extractor | daily."
- fail_example: "Source: SAP" with no table, object, owner or access method.

## FRD-XL-04: Source-to-target field mapping
- weight: high
- critical: true
- check: Every target field has its source system, source table and source field,
  and the transformation applied (or "direct" for a straight move). No target field
  is left without a source, and derived fields name every source field they use.
- pass_example: "Target: Invoice_Amount_INR | Source: RBKP.RMWWR, RBKP.WAERS | Transformation: convert to INR using TCURR rate on posting date."
- fail_example: Target fields listed with the source columns blank, or "from SAP" in place of a table and field.

## FRD-XL-05: Data types and formats
- weight: medium
- critical: false
- check: Source and target data types, lengths, precision and formats (dates,
  currency, codes) are stated, and type conversions are called out where they differ.
- pass_example: "RBKP.BUDAT: DATS (YYYYMMDD) → Posting_Date: DATE. RMWWR: CURR 13,2 → Invoice_Amount: DECIMAL(15,2)."
- fail_example: No data types given, or a date mapped from text with no format stated.

## FRD-XL-06: Transformation logic
- weight: high
- critical: false
- check: Every non-direct transformation is written precisely enough to implement
  without guessing, as a formula, pseudo-code or SQL expression, including how
  nulls, blanks and unexpected values are handled.
- pass_example: "Days_Overdue = MAX(0, Report_Date − Due_Date); if Due_Date is null, use Baseline_Date + payment term days."
- fail_example: "Derive overdue days", "clean the vendor name" or "as per business logic".

## FRD-XL-07: Keys and uniqueness
- weight: medium
- critical: false
- check: Primary or business keys are identified for each source and target, with
  how uniqueness is guaranteed and how duplicates are handled.
- pass_example: "Invoice key: BUKRS + BELNR + GJAHR. Duplicates from re-extraction removed by latest change timestamp."
- fail_example: No keys stated; the target table has no defined unique identifier.

## FRD-XL-08: Join definitions
- weight: high
- critical: false
- check: Every join states the left and right tables, join keys, join type (inner,
  left, etc.), expected cardinality (1:1, 1:N, N:1) and how unmatched or duplicate
  matches are handled.
- pass_example: "JN-03: RSEG LEFT JOIN EKKO ON RSEG.EBELN = EKKO.EBELN | N:1 | unmatched invoice lines kept with PO fields null and flagged 'No PO'."
- fail_example: "Join invoice and PO tables" with no keys, join type or cardinality.

## FRD-XL-09: Grain of each dataset
- weight: high
- critical: false
- check: The grain (what one row represents) is stated for each target table, view
  or dataset, and the joins and measures are consistent with it.
- pass_example: "Fact_Invoice_Line: one row per invoice line per company code. Fact_AP_Snapshot: one row per open item per day."
- fail_example: No grain stated, and measures that sum header-level amounts over a line-level table (double counting).

## FRD-XL-10: Filters, business rules and exclusions
- weight: high
- critical: false
- check: All filters and data-level business rules are stated explicitly: which
  records are included or excluded, by which field and value, and where in the flow
  the filter applies (source extract, model, report).
- pass_example: "Exclude reversed documents (RBKP.STBLG not blank). Include company codes IN01, IN02 only. Applied at extract."
- fail_example: "Exclude irrelevant records" or "only valid invoices" with no field or value.

## FRD-XL-11: Reference data, lookups and defaults
- weight: medium
- critical: false
- check: Lookup and reference tables (currency rates, calendars, code mappings) are
  identified with their source, and default values are defined for nulls,
  unmatched lookups and unknown codes.
- pass_example: "Vendor category from LFA1.KTOKK mapped via 'Vendor_Category_Map' sheet; unmapped codes shown as 'Unclassified'."
- fail_example: Fields mapped through a lookup that is not provided, and no rule for values that don't match.

## FRD-XL-12: Measure definitions
- weight: high
- critical: true
- check: Every measure or KPI has a name, business definition, exact calculation
  (formula, DAX or SQL), aggregation behaviour, filters or context it depends on,
  unit and display format. Time-intelligence measures (YTD, MoM, rolling) state the
  calendar and period logic.
- pass_example: "MSR-03 On-time Payment %: invoices paid on or before due date ÷ invoices paid in period. Calendar: fiscal (Apr–Mar). Format: %, 1 decimal."
- fail_example: "On-time %: percentage of invoices paid on time." with no formula, period or treatment of unpaid invoices.

## FRD-XL-13: Dimensions and hierarchies
- weight: medium
- critical: false
- check: Dimensions used for slicing are listed with their attributes, source and key,
  and hierarchies or drill paths are defined (e.g. Year > Quarter > Month,
  Region > Entity > Company code).
- pass_example: "Dim_Date: fiscal hierarchy FY > Quarter > Month > Day. Dim_Vendor: Category > Vendor, keyed on LIFNR."
- fail_example: Report filters by "region" and "period" with no dimension definition or hierarchy.

## FRD-XL-14: Report and visual mapping
- weight: medium
- critical: false
- check: For BI deliverables, each report page or visual is mapped to the measures,
  dimensions and filters it uses, so every element on the report traces to a
  defined measure or field.
- pass_example: "Page 1, visual 'AP Ageing by Bucket': measure MSR-05 by Dim_Ageing_Bucket; slicers: Company Code, Vendor Category."
- fail_example: Report mock-ups in the document with no indication of which measures or fields drive each visual.

## FRD-XL-15: Load and refresh
- weight: medium
- critical: false
- check: The load approach is defined for each dataset: full or incremental, the
  incremental key, refresh frequency and timing, latency, and how history and
  changes are kept (e.g. snapshots, SCD type).
- pass_example: "Fact_Invoice_Line: incremental on RBKP change date, daily 6 AM IST. Dim_Vendor: SCD Type 2 on vendor category."
- fail_example: No refresh frequency or load method, or "refresh as needed".

## FRD-XL-16: Data quality and reconciliation
- weight: medium
- critical: false
- check: Data quality checks are defined (completeness, validity, duplicates,
  referential integrity), with thresholds and what happens on failure, and the
  output reconciles to a named source total or report.
- pass_example: "Total invoice amount per company code per month must match SAP report S_ALR_87012082 within ₹1; mismatch alerts the BI support team."
- fail_example: No validation or reconciliation defined; no way to confirm the numbers are right.

## FRD-XL-17: Security and sensitive data
- weight: medium
- critical: false
- check: Row-level security rules and access groups are defined, and sensitive
  fields are identified with masking or exclusion rules.
- pass_example: "RLS: users see only company codes in their AD group mapping. Vendor bank account fields excluded from the model."
- fail_example: The dataset includes vendor bank details and all entities, with no access or masking rules.

## FRD-XL-18: Completeness of the workbook
- weight: medium
- critical: false
- check: Mandatory columns are filled on every row, and there are no "TBD", "?",
  placeholder or highlighted-for-review rows left unresolved. Open items are logged
  with an owner and date.
- pass_example: All mapping rows complete; two open items logged on the "Open_Items" sheet with owners and dates.
- fail_example: 30% of mapping rows have a blank transformation column; several cells say "TBD – check with SAP team".

## FRD-XL-19: Consistency with the document
- weight: medium
- critical: false
- check: Fields, measures, rules and reports referenced in the Word document exist in
  the workbook with matching names and logic, and the workbook does not contain
  rules that contradict the document.
- pass_example: Every measure named in FR-24 to FR-30 appears on the Measures sheet with the same name and definition.
- fail_example: The document defines overdue from due date, while the workbook calculates it from posting date; a KPI in the document is missing from the workbook.