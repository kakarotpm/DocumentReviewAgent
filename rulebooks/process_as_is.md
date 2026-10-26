---
doc_type: process_as_is
display_name: As-Is Process Document
pass_threshold: 80
description: Documents how a business process works today, including its problems and baseline performance.
---

## ASIS-01: Document control and sign-off
- weight: low
- critical: false
- check: The document has a title, version number, author, date and revision history,
  and a sign-off section naming the process owner and approvers (by name or role).
- pass_example: "v1.1, 07 May 2026, author: R. Iyer. Validated by: AP Team Lead. Approved by: Head of Finance Ops."
- fail_example: A revision history exists, but no process owner or approver is named anywhere.

## ASIS-02: Purpose and objectives
- weight: low
- critical: false
- check: The document states why the current process is being documented (e.g.
  baseline for improvement, SOP, audit, system replacement) and what readers should
  be able to do with it.
- pass_example: "Purpose: baseline the current invoice process ahead of the AP automation initiative and identify where time and errors occur."
- fail_example: No purpose stated; the document opens directly with process steps.

## ASIS-03: Process scope and boundaries
- weight: high
- critical: true
- check: The document states which processes and sub-processes are covered, the
  trigger that starts the process and the point where it ends, and what is
  explicitly out of scope (related processes, teams, regions or channels not covered).
- pass_example: "Starts when a supplier invoice is received by email or portal; ends when payment is released in SAP. Out of scope: payment runs, non-PO invoices, UAE entity."
- fail_example: "Covers the invoice lifecycle." with no start trigger, end point or exclusions.

## ASIS-04: Roles and responsibilities
- weight: high
- critical: false
- check: Every role that performs or approves work in the process is listed with its
  responsibilities, team and location where relevant. Headcount or capacity is
  given where it affects the process. Every actor named in the steps appears here.
- pass_example: "AP Clerk (6, Hyderabad): keys and matches invoices. AP Lead (1): resolves mismatches above ₹50K. Approver (budget holder): approves in email."
- fail_example: A roles table with empty rows for one region, or actors in the workflows (e.g. "Compliance team") who are never described.

## ASIS-05: Process overview and map
- weight: medium
- critical: false
- check: A high-level view shows all processes or sub-processes in scope and how
  they connect (e.g. a level-0/level-1 map or value chain), before the detailed
  workflows.
- pass_example: A one-page map: Receive → Capture → Match → Approve → Post → Pay, with the exception loop shown.
- fail_example: The document jumps straight into detailed workflows with no overview of how they fit together.

## ASIS-06: Process flow diagrams
- weight: high
- critical: false
- check: Each detailed workflow has a diagram that shows start and end points,
  steps, decision points and who performs each step (e.g. swimlanes), using a
  consistent notation, and the diagram matches the written steps.
- pass_example: A swimlane diagram with lanes for Supplier, AP Clerk, Approver and SAP, with diamonds for "PO match?" and "Within tolerance?".
- fail_example: No diagrams, or diagrams with no start/end, no actors and steps that differ from the narrative.

## ASIS-07: Step-by-step process description
- weight: high
- critical: true
- check: Each workflow is described as numbered, sequential steps. Each step states
  who does it, what they do and in which system or tool, in enough detail that a
  new team member could follow it.
- pass_example: "Step 4: AP Clerk opens the invoice in SAP (MIRO) and enters PO number, amount and GST details."
- fail_example: "The team processes the invoice and gets it approved." (no actors, systems or sequence).

## ASIS-08: Triggers, inputs and outputs
- weight: medium
- critical: false
- check: For each workflow, the document states what triggers it, what inputs it
  needs (documents, data, requests) and what it produces (records, updates,
  communications, handoffs).
- pass_example: "Trigger: invoice email in AP inbox. Inputs: invoice PDF, PO, goods receipt. Output: posted invoice in SAP, approval record."
- fail_example: Workflows start at "Step 1: open the ticket" with no indication of where work comes from or what it produces.

## ASIS-09: Decision points and business rules
- weight: high
- critical: false
- check: Every decision in the process is stated with the condition that decides
  each path. Thresholds, eligibility criteria and rules are specific, not left to
  judgement phrases such as "if needed", "as appropriate" or "any other relevant
  factors". Where judgement truly applies, the document says who makes it and on
  what basis.
- pass_example: "If invoice amount differs from PO by more than 2% or ₹10,000, route to AP Lead; otherwise auto-approve."
- fail_example: "High amounts may trigger a review." or "Check other eligibility criteria and any other relevant factors."

## ASIS-10: Exceptions and error handling
- weight: medium
- critical: false
- check: The document describes what happens when things go wrong or fall outside
  the normal path: missing information, rejections, system failures, no response
  from a party, rework loops, and how they are resolved.
- pass_example: "If the supplier does not respond to a query within 5 working days, the clerk sends one reminder, then escalates to Procurement."
- fail_example: Only the happy path is described; "wait for response" has no time limit or fallback.

## ASIS-11: Handoffs and escalations
- weight: medium
- critical: false
- check: Handoffs between people, teams, regions or systems are identified, including
  how work is passed (tool, channel), and escalation paths state the trigger, who it
  goes to and expected response time.
- pass_example: "Mismatches above ₹50K are escalated to the AP Lead via a Jira ticket; AP Lead responds within 1 working day."
- fail_example: "Complex cases are escalated to the global team." with no trigger, recipient or mechanism.

## ASIS-12: Systems and tools
- weight: medium
- critical: false
- check: All systems and tools used in the process are listed with their purpose,
  and each is linked to the steps where it is used. Manual workarounds
  (spreadsheets, personal documents, email) are captured, not just official systems.
- pass_example: "SAP: posting and matching. Shared mailbox: intake. Excel tracker (AP Lead): manual log of disputed invoices."
- fail_example: A tools table that omits tools named in the workflows, or no mention of the spreadsheets the team actually relies on.

## ASIS-13: Data and documents
- weight: low
- critical: false
- check: The key data, records and documents used or created in the process are
  identified, with where they are held and who owns them.
- pass_example: "Invoice PDF (shared drive, 8-year retention), vendor master (SAP, owned by Procurement)."
- fail_example: No mention of what data the process depends on or where it lives.

## ASIS-14: Volumes, frequency and effort
- weight: high
- critical: false
- check: The document gives current volumes and frequency for each main workflow
  (e.g. per day/month), and effort or cycle time where available, with the source
  and period of the figures.
- pass_example: "~4,000 invoices/month (SAP, Jan–Mar 2026); average handling time 12 min; 15% need rework."
- fail_example: No volumes or timings, or a single figure for one team with no source or period.

## ASIS-15: Performance measures and SLAs
- weight: medium
- critical: false
- check: Current SLAs, KPIs or targets are stated for the process, with whether
  they measure response or resolution, and current performance against them where
  known.
- pass_example: "SLA: approve within 5 working days of receipt. Current: 62% met (Q4 2025)."
- fail_example: SLAs mentioned for some request types but not others, with no indication of whether they are being met.

## ASIS-16: Pain points and issues
- weight: high
- critical: true
- check: The document identifies the problems in the current process: delays,
  rework, manual effort, errors, bottlenecks, control gaps, user or customer
  complaints. Each is tied to the step or workflow where it occurs and, where
  possible, its impact is quantified.
- pass_example: "Step 6 (manual approval by email): approvals wait an average of 4 days; 9% of invoices are paid late as a result."
- fail_example: No pain points section, or a generic line such as "The process is manual and slow."

## ASIS-17: Controls and compliance
- weight: medium
- critical: false
- check: The document identifies the controls in the process (approvals, checks,
  segregation of duties, audit trails, privacy safeguards) and any regulatory or
  policy requirements the process must meet.
- pass_example: "Clerk who keys the invoice cannot approve it (SoD). GST number validated before posting. Audit trail kept in SAP change log."
- fail_example: No mention of approvals, checks or compliance, for a process handling payments or personal data.

## ASIS-18: Variations across regions, teams or channels
- weight: medium
- critical: false
- check: Where the process differs by region, team, channel, product or customer
  type, the variations are documented, or the document states that the process is
  the same everywhere.
- pass_example: "UAE entity follows the same flow except approvals above AED 20K also need the Country Controller."
- fail_example: The document covers one region in detail and notes "global process may differ" without describing how.

## ASIS-19: Current state stays distinct from future state
- weight: medium
- critical: false
- check: The workflows describe how work is actually done today, not how it should
  be done. Improvement ideas, if included, are kept in a separate, clearly labelled
  section rather than mixed into the process description.
- pass_example: Process sections describe current steps only; a separate "Improvement opportunities" section lists ideas.
- fail_example: Workflow steps interleaved with "this should be automated" or "the new tool will handle this".

## ASIS-20: Improvement opportunities linked to pain points
- weight: low
- critical: false
- check: If improvement opportunities are included, each is linked to a specific
  pain point and gives an indication of expected benefit (time, cost, quality, risk).
- pass_example: "Auto-route approvals in SAP workflow (addresses pain point P-03; estimated saving 3 days per invoice)."
- fail_example: A list of automation ideas with no link to identified problems and no expected benefit.

## ASIS-21: Sources and validation
- weight: low
- critical: false
- check: The document states how the current state was captured (interviews,
  workshops, observation, system data, existing SOPs), who contributed, and that
  the people who do the work have validated it.
- pass_example: "Based on 4 interviews and 2 shadowing sessions with AP clerks (Mar 2026); walkthrough validated with AP Lead on 10 Apr."
- fail_example: No indication of where the information came from or whether the team doing the work has reviewed it.

## ASIS-22: Completeness (no placeholders)
- weight: medium
- critical: false
- check: The document contains no unfinished sections: no empty tables or headings,
  "TBD", "need inputs here", or missing diagrams referenced in the text. Open items,
  if any, are listed with an owner and target date.
- pass_example: All sections populated; one open item logged: "UAE approval limit – owner: UAE Controller, due 30 Nov."
- fail_example: A roles table with blank rows and a section that reads "(Need global inputs here)".

## ASIS-23: Internal consistency
- weight: medium
- critical: false
- check: Section and step numbering is correct and sequential, the table of contents
  matches the body, diagrams match the written steps, and names of roles, tools,
  SLAs and figures are consistent across sections.
- pass_example: Steps numbered 1–14 without repeats; every tool named in the workflows appears in the tools table.
- fail_example: Two sections numbered 6; a workflow whose steps jump from 17 back to 11; a tool used in the steps that is missing from the tools list.