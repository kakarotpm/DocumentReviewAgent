---
doc_type: process_to_be
display_name: To-Be Process Document
pass_threshold: 80
description: Describes the future-state process, what changes from today, and how improvement will be measured.
---

## TOBE-01: Document control and As-Is reference
- category: Structure
- weight: low
- critical: false
- check: The document has a title, version, author, date and revision history, and
  references the As-Is process document it improves on (by name or version).
- pass_example: "To-Be: Supplier Onboarding v1.0. Based on As-Is: Supplier Onboarding v1.0 (10 Jun 2026)."
- fail_example: No version or date, and no mention of the As-Is document.

## TOBE-02: Future-state process map
- category: Structure
- weight: medium
- critical: false
- check: A future-state process map or swimlane diagram is included or clearly referenced.
- pass_example: "Figure 2: To-Be swimlane (onboarding_tobe_v1.vsdx)."
- fail_example: No diagram and no reference to one.

## TOBE-03: What changes and why
- category: Change
- weight: high
- critical: true
- check: The document clearly states what is different from the As-Is process (steps
  added, removed, automated or moved) and the reason for each change. Changes listed
  without reasons are partially met.
- pass_example: "Bank verification moves from manual check to automated API validation, removing the 3–5 day wait for rework."
- fail_example: A To-Be process described on its own with no comparison to today.

## TOBE-04: Pain points addressed
- category: Change
- weight: high
- critical: true
- check: Each pain point from the As-Is document is listed with how the To-Be process
  addresses it (or why it is not addressed). Covering only some pain points is partially met.
- pass_example: "Pain point: duplicate supplier records → resolved by a duplicate check on tax ID at request submission."
- fail_example: Pain points are not mentioned.

## TOBE-05: Role and responsibility changes
- category: Roles
- weight: medium
- critical: false
- check: Changes to who does what are stated: new, removed or changed roles and
  responsibilities.
- pass_example: "Procurement Analysts no longer verify bank details; they handle only exceptions flagged by the system."
- fail_example: Roles are not discussed.

## TOBE-06: System changes
- category: Systems
- weight: medium
- critical: false
- check: New systems, system changes, and retired tools are listed.
- pass_example: "New: supplier portal. Changed: SAP vendor creation via API. Retired: Supplier Tracker spreadsheet."
- fail_example: No mention of systems.

## TOBE-07: Controls and compliance
- category: Governance
- weight: medium
- critical: false
- check: Controls and compliance checkpoints in the new process are identified (approvals,
  segregation of duties, audit trail, regulatory checks).
- pass_example: "Control: vendor creation requires approval by someone other than the requester; all changes logged for audit."
- fail_example: No controls mentioned.

## TOBE-08: Target KPIs against baseline
- category: Metrics
- weight: high
- critical: false
- check: Target KPIs are stated and compared with the As-Is baseline values. Targets
  without baselines are partially met.
- pass_example: "Cycle time: 11 days (As-Is) → 3 days (target). Rework: 18% → under 5%."
- fail_example: "The process will be faster."

## TOBE-09: Change impact and transition
- category: Change
- weight: medium
- critical: false
- check: The document describes how the organisation moves to the new process: who is
  impacted, training, communications, cut-over or phasing.
- pass_example: "Pilot with UK buyers in September, all regions from November; 1-hour training for 40 buyers."
- fail_example: No mention of transition or impact.
