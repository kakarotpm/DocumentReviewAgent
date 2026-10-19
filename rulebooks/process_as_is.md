---
doc_type: process_as_is
display_name: As-Is Process Document
pass_threshold: 80
description: Documents how a business process works today, including its problems and baseline performance.
---

## ASIS-01: Document control
- category: Structure
- weight: low
- critical: false
- check: The document has a title, version number, author, date and revision history.
- pass_example: "As-Is: Supplier Onboarding, v1.0, 10 Jun 2026, author: M. Okafor."
- fail_example: No version, author or date.

## ASIS-02: Scope and boundaries
- category: Scope
- weight: high
- critical: true
- check: The process scope is clear: the trigger that starts it, the point where it ends,
  and what is included and excluded. Missing either the start or the end is partially met.
- pass_example: "Starts when a buyer submits a new-supplier request; ends when the supplier is active in the ERP. Excludes supplier contract negotiation."
- fail_example: "This document describes supplier onboarding."

## ASIS-03: Actors and roles
- category: Roles
- weight: medium
- critical: false
- check: Every person, team or external party involved in the process is identified with
  what they do.
- pass_example: "Buyer (raises request), Procurement Analyst (checks documents), Finance Master Data (creates vendor record)."
- fail_example: Steps describe actions without saying who performs them.

## ASIS-04: Process map
- category: Structure
- weight: medium
- critical: false
- check: A process map or swimlane diagram is included or clearly referenced (with a
  location or filename).
- pass_example: "See Figure 1: swimlane diagram (Visio file: onboarding_asis_v1.vsdx)."
- fail_example: No diagram and no reference to one.

## ASIS-05: Steps with inputs and outputs
- category: Process Detail
- weight: high
- critical: false
- check: The process is described step by step in order, and each step states its inputs
  and outputs. Steps without inputs/outputs are partially met.
- pass_example: "Step 3: Analyst checks bank details. Input: supplier form + bank letter. Output: verified form or rejection email."
- fail_example: "The team processes the request and sets up the supplier."

## ASIS-06: Systems and tools
- category: Process Detail
- weight: medium
- critical: false
- check: The systems, tools and documents used at each step are named (including
  spreadsheets, email and paper).
- pass_example: "Step 2 uses the shared mailbox and the Supplier Tracker spreadsheet; Step 5 uses SAP transaction XK01."
- fail_example: No systems or tools mentioned.

## ASIS-07: Exceptions and workarounds
- category: Process Detail
- weight: medium
- critical: false
- check: Exceptions, rework loops and informal workarounds are described, not only the
  happy path.
- pass_example: "If bank details fail verification (~15% of cases), the analyst emails the buyer and the request waits, often 3–5 days."
- fail_example: Only the standard path is described.

## ASIS-08: Evidenced pain points
- category: Problems
- weight: high
- critical: true
- check: Pain points are listed and each is backed by evidence or a number (volume, time,
  cost, error rate, complaint count). Pain points without evidence are partially met.
- pass_example: "Duplicate supplier records: 340 found in the 2025 audit, causing 12 duplicate payments."
- fail_example: "The process is slow and frustrating."

## ASIS-09: Baseline metrics
- category: Metrics
- weight: high
- critical: false
- check: Baseline performance is quantified: at least volume and cycle time, and ideally
  error rate or cost, with the source and period of the data.
- pass_example: "Volume 120 requests/month; average cycle time 11 working days; 18% rework rate (Jan–Jun 2026, Supplier Tracker)."
- fail_example: No metrics, or metrics without a source or period.
