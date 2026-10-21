---
doc_type: brd
display_name: Business Requirements Document
pass_threshold: 80
description: Captures the business need, objectives, scope and high-level requirements.
---

## BRD-01: Document control and sign-off
- weight: low
- critical: false
- check: The document has a title, version number, author, date and revision history,
  and a sign-off section naming the approvers (by name or role).
- pass_example: "v1.2, 14 Mar 2026, author: J. Patel. Approvers: Head of Finance Ops, IT Delivery Lead."
- fail_example: A title page with no version, date, revision history or approvers.

## BRD-02: Business context and problem
- weight: medium
- critical: false
- check: The document explains why the project exists: the business problem or opportunity,
  the current state, and who is affected. A reader new to the project understands the need.
- pass_example: "Invoices are keyed manually from PDFs; 4 FTEs spend ~60% of their time on data entry and 7% of invoices contain errors."
- fail_example: "This project will implement a new invoicing system."

## BRD-03: Measurable business objectives
- weight: high
- critical: true
- check: The document states business objectives that are specific and measurable, each with
  a target value and a timeframe. Objectives without a number or a date are only partially met.
- pass_example: "Reduce invoice processing cost by 20% within 12 months of go-live."
- fail_example: "Improve the invoicing process."

## BRD-04: Scope in and out
- weight: high
- critical: true
- check: The document explicitly lists both what is in scope and what is out of scope.
  Listing only in-scope items is partially met.
- pass_example: "In scope: supplier invoices in GBP and EUR. Out of scope: expense claims; historical invoices before 2024."
- fail_example: A scope section that lists features to be delivered but never states exclusions.

## BRD-05: Stakeholders and roles
- weight: medium
- critical: false
- check: Stakeholders are identified with their role and responsibility on the project
  (for example a RACI table or a stakeholder list with responsibilities).
- pass_example: "Finance Ops Manager (Accountable, approves requirements); AP Clerks (Consulted, UAT testers)."
- fail_example: "Stakeholders: Finance, IT."

## BRD-06: Requirements uniquely identified and prioritised
- weight: medium
- critical: false
- check: Every business requirement has a unique ID and a priority (for example MoSCoW or
  High/Medium/Low). Requirements with IDs but no priorities are partially met.
- pass_example: "BR-07 (Must): The system shall match invoices to purchase orders automatically."
- fail_example: A bulleted list of requirements with no IDs or priorities.

## BRD-07: Requirements are clear, testable and business-level
- weight: high
- critical: false
- check: Requirements describe business needs, not technical solution design. Each one is
  unambiguous and testable. Vague terms such as "fast", "user-friendly", "easy", "etc." are
  not used unless defined with a measurable meaning.
- pass_example: "BR-12: Approvers must be able to approve an invoice within 2 business days of receipt."
- fail_example: "The system should be fast and user-friendly and use a microservices architecture."

## BRD-08: Assumptions, constraints and dependencies
- weight: medium
- critical: false
- check: The document lists assumptions, constraints (budget, time, regulatory, technical)
  and dependencies on other projects, teams or systems.
- pass_example: "Constraint: must go live before the financial year-end on 31 March. Dependency: ERP upgrade (Project Atlas) completes in Q4."
- fail_example: No assumptions, constraints or dependencies mentioned anywhere.

## BRD-09: Risks with mitigations
- weight: low
- critical: false
- check: Key risks are identified and each has a mitigation or owner. Risks without
  mitigations are partially met.
- pass_example: "Risk: supplier data quality is poor. Mitigation: data cleansing sprint before migration, owned by AP Lead."
- fail_example: "Risks: TBD."

## BRD-10: Success metrics and KPIs
- weight: medium
- critical: false
- check: The document defines how success will be measured after delivery: KPIs, their
  baseline and target, and how or when they will be measured.
- pass_example: "KPI: average invoice cycle time. Baseline 9 days, target 3 days, measured monthly from the AP dashboard."
- fail_example: "Success will be determined by user satisfaction."
