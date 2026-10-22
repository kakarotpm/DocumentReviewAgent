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

## BRD-02: Executive summary
- weight: medium
- critical: false
- check: A short summary near the start states the problem, the intended outcome,
  the scope at a high level and the expected benefit, readable on its own by a
  senior stakeholder without reading the rest of the document.
- pass_example: "Finance Ops manually keys ~4,000 supplier invoices a month. This initiative automates capture and matching to cut processing time by 60% and late-payment penalties to near zero within FY27."
- fail_example: An introduction that only describes the company or the project name, with no problem, outcome or benefit.

## BRD-03: Business problem or opportunity statement
- weight: high
- critical: true
- check: The document clearly states the business problem or opportunity being
  addressed, who is affected, and the evidence or impact (cost, time, risk, revenue,
  customer experience). The problem is described in business terms, not as a
  missing system or feature.
- pass_example: "Invoices take an average of 9 days to approve; 12% are paid late, costing ~₹38L a year in penalties and straining supplier relationships."
- fail_example: "We need a new OCR tool." (states a solution, not a problem, and gives no impact.)

## BRD-04: Measurable business objectives
- weight: high
- critical: true
- check: Business objectives are listed and are specific and measurable, each with
  a target value and a timeframe. Each objective links back to the problem statement.
- pass_example: "OBJ-1: Reduce average invoice approval time from 9 days to 3 days by Q2 FY27."
- fail_example: "Improve efficiency and make the process faster."

## BRD-05: In-scope definition
- weight: high
- critical: true
- check: The scope section explicitly lists what is included: business processes,
  business units, geographies, user groups, channels and products covered.
- pass_example: "In scope: PO-backed supplier invoices for India and UAE entities, received by email or supplier portal."
- fail_example: "Scope: the invoice process." with no boundaries stated.

## BRD-06: Out-of-scope definition
- weight: medium
- critical: false
- check: The document explicitly lists what is excluded, so readers can tell where
  the initiative stops. Exclusions are specific, not generic.
- pass_example: "Out of scope: non-PO invoices, employee expense claims, and US entities (planned for phase 2)."
- fail_example: No out-of-scope section, or "Anything not mentioned above."

## BRD-07: Stakeholders and roles
- weight: medium
- critical: false
- check: Stakeholders are identified by name or role, with their interest or
  involvement in the initiative. Decision-makers and the business owner/sponsor
  are clearly identified. A RACI or equivalent is a plus.
- pass_example: "Sponsor: CFO. Business owner: Head of Finance Ops. Consulted: Procurement, Internal Audit. Informed: Supplier Relations."
- fail_example: "Stakeholders: Finance team, IT team."

## BRD-08: Current state summary
- weight: medium
- critical: false
- check: The document describes how the business works today for the in-scope area,
  including key pain points, volumes and who is involved, in enough detail to
  justify the requirements. A link to a separate As-Is document is acceptable if a
  brief summary is also given.
- pass_example: "Invoices arrive by email, are keyed into SAP by 6 AP clerks, and routed for approval by email. Mismatches are resolved by phone. Volume: ~4,000/month."
- fail_example: No description of the current process; requirements appear without context.

## BRD-09: Business requirements are stated and uniquely identified
- weight: high
- critical: true
- check: Business requirements are listed individually, each with a unique ID, and
  each describes a business need or capability (what the business must be able to
  do), not a technical design.
- pass_example: "BR-04: Finance Ops must be able to see all invoices awaiting approval, by approver and age."
- fail_example: Requirements written as a paragraph of prose with no IDs, or a single bullet saying "System should handle invoices."

## BRD-10: Requirements are clear and verifiable
- weight: high
- critical: false
- check: Each requirement is unambiguous and could be verified. Vague terms such as
  "fast", "user-friendly", "easy", "flexible", "robust", "as appropriate" or "etc."
  are absent or quantified. Each requirement expresses one need (not several joined
  by "and/or").
- pass_example: "BR-07: Invoices matching the PO within 2% tolerance must be approved without manual review."
- fail_example: "BR-07: The process should be quick and user-friendly and handle exceptions etc."

## BRD-11: Solution-neutral language
- weight: medium
- critical: false
- check: Requirements describe needs and outcomes rather than prescribing specific
  technology, screens, vendors or implementation details, unless a constraint
  genuinely mandates it (and is recorded as a constraint).
- pass_example: "BR-02: Invoice data must be captured without manual keying for standard-format invoices."
- fail_example: "BR-02: Build a React screen with an ABBYY OCR integration and a dropdown for supplier."

## BRD-12: Success measures and KPIs
- weight: high
- critical: false
- check: The document defines how success will be measured after go-live, with
  KPIs that have a current baseline, a target, a data source and an owner.
- pass_example: "KPI: % invoices paid on time. Baseline 88% (Jan–Mar 2026, SAP report). Target 98%. Owner: AP Manager."
- fail_example: "Success: users are happy with the new process."

## BRD-13: Assumptions
- weight: medium
- critical: false
- check: Assumptions the requirements depend on are listed explicitly, are specific,
  and ideally note what happens if the assumption proves false.
- pass_example: "A-02: Suppliers above ₹10L annual spend will adopt the portal by go-live; if not, email intake must stay in scope."
- fail_example: No assumptions section, or "We assume everything will go to plan."

## BRD-14: Constraints
- weight: medium
- critical: false
- check: Known constraints are stated: budget, deadlines, regulatory, technology
  mandates, resourcing or policy limits.
- pass_example: "C-01: Must use the existing SAP S/4HANA instance. C-02: Go-live before 31 Mar 2027 for audit cycle."
- fail_example: No constraints mentioned, although the document elsewhere refers to a fixed deadline and mandated system.

## BRD-15: Dependencies
- weight: medium
- critical: false
- check: Dependencies on other projects, teams, systems, vendors or decisions are
  listed, with the owner of each where known.
- pass_example: "D-01: Vendor master data cleanup (Procurement, due Nov 2026) must complete before matching rules go live."
- fail_example: No dependencies listed for an initiative that clearly relies on other teams or systems.

## BRD-16: Risks and mitigations
- weight: medium
- critical: false
- check: Business risks are identified with likelihood or impact and a mitigation
  or owner for each.
- pass_example: "R-03: AP clerks resist change (Medium/High). Mitigation: involve 2 clerks in UAT, phased rollout. Owner: Finance Ops Lead."
- fail_example: "Risks: delays, budget overrun." with no impact, mitigation or owner.

## BRD-17: Regulatory, compliance and data considerations
- weight: medium
- critical: false
- check: The document states applicable regulatory, legal, audit, data privacy and
  data retention requirements, or explicitly states that none apply.
- pass_example: "Invoices must be retained 8 years per Companies Act; GST fields must be validated; supplier bank details are restricted data."
- fail_example: No mention of compliance or data handling for a process involving financial or personal data.

## BRD-18: Business impact and change considerations
- weight: medium
- critical: false
- check: The document describes how the change affects people, processes, policies,
  other teams and systems, including training, communication or organisational
  changes needed.
- pass_example: "AP clerks move from data entry to exception handling; approval policy to be updated; 2 training sessions per region."
- fail_example: No discussion of who or what is affected beyond the requirements list.

## BRD-19: Timeline and milestones
- weight: low
- critical: false
- check: High-level target dates or phases are given (e.g. requirements sign-off,
  build, UAT, go-live), consistent with any stated constraints.
- pass_example: "Phase 1 (India) go-live Feb 2027; Phase 2 (UAE) May 2027."
- fail_example: No dates or phases, or "ASAP".

## BRD-20: Glossary and acronyms
- weight: low
- critical: false
- check: Business terms, acronyms and domain jargon used in the document are defined
  in a glossary or on first use.
- pass_example: "3-way match: matching invoice, PO and goods receipt before payment."
- fail_example: Terms like "GRN", "3WM" and "AP aging" used throughout with no definition.

## BRD-21: Open issues and decisions log
- weight: low
- critical: false
- check: Unresolved questions and pending decisions are recorded, each with an owner
  and target date, rather than left implicit or marked "TBD" inside requirements.
- pass_example: "OI-03: Approval threshold for UAE entity – owner: UAE Controller, due 30 Nov 2026."
- fail_example: Multiple "TBD" placeholders scattered through requirements with no owner or tracking.

## BRD-22: Internal consistency
- weight: medium
- critical: false
- check: Figures, names, IDs, dates and scope statements are consistent across
  sections. Requirements do not contradict each other or fall outside the stated scope.
- pass_example: Volumes, entity names and the go-live date match in the summary, scope, KPIs and timeline.
- fail_example: Summary says 4,000 invoices/month, KPIs say 2,500; a requirement covers US entities which are listed as out of scope.