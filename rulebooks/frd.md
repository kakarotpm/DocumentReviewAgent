---
doc_type: frd
display_name: Functional Requirements Document
pass_threshold: 80
description: Describes in detail what the system must do to meet the business requirements.
---

## FRD-01: Document control and sign-off
- category: Structure
- weight: low
- critical: false
- check: The document has a title, version number, author, date, revision history, and a
  sign-off section naming the approvers.
- pass_example: "v0.9, 2 May 2026, author: A. Chen. Approvers: Product Owner, Solution Architect."
- fail_example: No version, date or approvers anywhere in the document.

## FRD-02: Unique IDs traced to the BRD
- category: Traceability
- weight: high
- critical: true
- check: Every functional requirement has a unique ID and references the BRD requirement ID(s)
  it delivers (inline or in a traceability matrix). Requirements with IDs but missing BRD
  references are partially met.
- pass_example: "FR-031 (traces to BR-07): The system shall auto-match an invoice to a PO when supplier, PO number and amount match."
- fail_example: Functional requirements listed without IDs or any link back to the BRD.

## FRD-03: Use cases or user stories with acceptance criteria
- category: Requirements Quality
- weight: high
- critical: true
- check: Functional behaviour is described as use cases or user stories, and each has
  acceptance criteria that can be tested. Stories without acceptance criteria are partially met.
- pass_example: "As an AP clerk I want unmatched invoices flagged so I can resolve them. AC: Given an invoice with no PO match, when it is imported, then it appears in the Exceptions queue within 5 minutes."
- fail_example: "Users can manage invoices."

## FRD-04: Business rules stated explicitly
- category: Requirements Quality
- weight: medium
- critical: false
- check: Business rules (calculations, conditions, thresholds, policies) are stated
  explicitly and unambiguously, ideally with IDs.
- pass_example: "BRule-04: Invoices over £10,000 require a second approver from Finance."
- fail_example: "Approval rules will follow company policy."

## FRD-05: Data requirements
- category: Data
- weight: medium
- critical: false
- check: Key data entities and fields are listed with type, mandatory/optional, and
  validation rules.
- pass_example: "Invoice Number: text, max 20 chars, mandatory, unique per supplier."
- fail_example: "The system will store invoice data."

## FRD-06: Interfaces and integrations
- category: Integration
- weight: medium
- critical: false
- check: Each interface with another system names the system, the data exchanged, the
  direction, the frequency or trigger, and the method (API, file, etc.).
- pass_example: "ERP → DocReview: approved POs, nightly batch via SFTP CSV at 02:00."
- fail_example: "The system will integrate with the ERP."

## FRD-07: UI and reporting requirements
- category: Requirements Quality
- weight: low
- critical: false
- check: Screens, key UI behaviours, and reports are described (wireframes referenced, or
  fields, filters and outputs listed).
- pass_example: "Report R-02: Aged exceptions by supplier, filterable by date range, exportable to Excel."
- fail_example: No mention of screens or reports.

## FRD-08: Error and exception handling
- category: Requirements Quality
- weight: medium
- critical: false
- check: The document states what happens when things go wrong: validation failures,
  integration failures, timeouts, and the messages or actions shown to users.
- pass_example: "If the ERP feed fails, retry 3 times at 10-minute intervals, then alert the support mailbox."
- fail_example: Only the happy path is described.

## FRD-09: Measurable non-functional requirements
- category: Non-Functional
- weight: high
- critical: false
- check: Non-functional requirements (performance, security, availability, accessibility)
  are stated with measurable targets. Unquantified NFRs are partially met.
- pass_example: "Search results return in under 2 seconds for 95% of queries; 99.5% availability during business hours."
- fail_example: "The system must be secure and perform well."

## FRD-10: Assumptions and dependencies
- category: Governance
- weight: low
- critical: false
- check: Assumptions and dependencies (other systems, teams, data, decisions) are listed.
- pass_example: "Assumes the ERP PO API is available in the test environment by Sprint 3."
- fail_example: No assumptions or dependencies mentioned.
