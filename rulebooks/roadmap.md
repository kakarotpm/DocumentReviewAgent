---
doc_type: roadmap
display_name: Product / Project Roadmap
pass_threshold: 80
description: Sets out the vision, initiatives, timeline and milestones for a product or project.
---

## RM-01: Document control and ownership
- weight: low
- critical: false
- check: The document has a title, version number, date, a named product owner and
  revision history, and states who has approved the roadmap (by name or role).
- pass_example: "AP Automation Roadmap v1.3, 05 Oct 2026. Product owner: M. Shah. Approved by: CFO, Head of Finance Ops."
- fail_example: A title with no version, date, owner or approvers.

## RM-02: Vision and strategic alignment
- weight: medium
- critical: false
- check: The roadmap states a product vision and explains how the product supports
  named business strategies, objectives or OKRs.
- pass_example: "Vision: zero-touch processing for standard supplier invoices. Supports FY27 objective 'Finance cost-to-serve down 20%'."
- fail_example: A vision statement with no link to any business goal or strategy.

## RM-03: Problem and target users
- weight: high
- critical: true
- check: The roadmap identifies the users or customers it serves and the problem it
  solves for them, with evidence of the problem's size (volumes, effort, cost,
  satisfaction, complaints).
- pass_example: "Users: 6 AP clerks and 40 approvers. Problem: 4,000 invoices/month keyed manually; 9-day average approval; 12% paid late."
- fail_example: "This product will transform the way the team works." with no users, problem or evidence.

## RM-04: Measurable outcomes and KPIs
- weight: high
- critical: true
- check: The roadmap defines the outcomes it aims to achieve as KPIs with a current
  baseline, a target and a timeframe, ideally per phase, and states how and from
  where each KPI will be measured.
- pass_example: "Automation rate: baseline 0%, target 40% by end of Phase 2, 70% by end of Phase 3 (source: workflow logs)."
- fail_example: KPIs listed only as directions, such as "reduce resolution time" or "increase automation rate", with no baseline or target.

## RM-05: Phases or releases with clear goals
- weight: high
- critical: true
- check: The roadmap is organised into phases, releases or horizons, each with a
  stated goal or theme explaining what that stage achieves, not just a list of items.
- pass_example: "Phase 1 – Capture: eliminate manual keying for PO invoices. Phase 2 – Match: auto-approve within-tolerance invoices."
- fail_example: A single list of features with no grouping or goal per stage.

## RM-06: Capabilities defined per phase
- weight: high
- critical: false
- check: Each phase lists the capabilities or features it delivers, each described
  clearly enough to understand what it does and who benefits. Coverage of use cases,
  segments or request types per phase is explicit.
- pass_example: "Phase 1: invoice capture from email and portal (AP clerks); duplicate invoice detection; capture dashboard for AP Lead."
- fail_example: Phase items such as "AI enhancements" or "integration improvements" with no description.

## RM-07: Prioritisation rationale
- weight: high
- critical: false
- check: The roadmap explains why items are sequenced as they are, using evidence
  such as volume, value, effort, risk or dependencies, so readers can see why one
  item comes before another.
- pass_example: "PO invoices first: 78% of volume and lowest complexity. Non-PO invoices in Phase 3 due to approval policy dependency."
- fail_example: Items assigned to phases with no explanation of why.

## RM-08: Timeline and horizons
- weight: medium
- critical: false
- check: Each phase has target dates or a duration anchored to a stated start date,
  and the roadmap distinguishes committed near-term items from less certain later
  ones (e.g. Now/Next/Later or confidence levels).
- pass_example: "Phase 1: Jan–Mar 2027 (committed). Phase 2: Apr–Jun 2027 (planned). Phase 3: H2 2027 (indicative)."
- fail_example: "Months 1–3, 4–6, 7–9" with no start date or level of certainty.

## RM-09: Scope boundaries and future considerations
- weight: medium
- critical: false
- check: The roadmap states what is not included in the planned phases and lists
  deferred or future ideas separately from committed scope.
- pass_example: "Not in scope: payment runs, non-AP finance processes. Future: supplier self-service portal, predictive cash-flow alerts."
- fail_example: No exclusions stated, and future ideas mixed into the phase lists.

## RM-10: Dependencies
- weight: high
- critical: false
- check: Dependencies on other teams, systems, data access, vendors, decisions or
  projects are listed, with which phase they affect and who owns them.
- pass_example: "Phase 2 depends on SAP workflow API access (SAP CoE, due Feb 2027) and vendor master cleanup (Procurement)."
- fail_example: Phases rely on integrations with several systems, but no dependencies or owners are listed.

## RM-11: Risks and mitigations
- weight: medium
- critical: false
- check: Key risks to delivery or adoption are identified with impact and a
  mitigation or owner.
- pass_example: "Risk: OCR accuracy below 95% on handwritten invoices (High). Mitigation: route low-confidence captures to manual review."
- fail_example: No risks mentioned.

## RM-12: Assumptions and constraints
- weight: medium
- critical: false
- check: Assumptions the plan depends on and constraints that shape it (budget,
  team size, technology, regulation, deadlines) are stated.
- pass_example: "Assumes 2 developers and 1 data engineer through Phase 3. Constraint: must run on existing Azure tenancy."
- fail_example: No assumptions or constraints, though timelines clearly depend on team capacity and system access.

## RM-13: Phase exit criteria
- weight: medium
- critical: false
- check: Each phase states the criteria for considering it complete or moving to the
  next phase (go/no-go), such as KPI thresholds, quality levels or user sign-off.
- pass_example: "Exit Phase 1 when capture accuracy ≥ 95% for 4 consecutive weeks and AP Lead signs off."
- fail_example: Phases simply follow each other by date, with no criteria for readiness.

## RM-14: Ownership, resources and stakeholders
- weight: medium
- critical: false
- check: The roadmap names who owns delivery of each phase or initiative, the teams
  or resources involved, and the key stakeholders to be consulted or informed.
- pass_example: "Phase 1 owner: AP Product Lead. Delivery: Automation squad (4 FTE). Stakeholders: Finance Ops, Internal Audit, Procurement."
- fail_example: No owners, teams or stakeholders named.

## RM-15: Systems and data landscape
- weight: medium
- critical: false
- check: The systems and data sources the product relies on are listed with their
  purpose and the phase in which each is needed, ideally with a context or
  architecture diagram.
- pass_example: "SAP S/4HANA (PO and GRN data, Phase 1), supplier portal (invoice intake, Phase 1), Azure AD (login, Phase 1)." Diagram included.
- fail_example: A list of system names with no purpose stated, or systems with blank descriptions.

## RM-16: User experience and adoption
- weight: medium
- critical: false
- check: The roadmap describes how the user experience changes across phases and how
  adoption will be supported: rollout approach, pilots, training and communication.
- pass_example: "Phase 1 piloted with 2 clerks for 4 weeks, then full rollout; 1-hour training per region; weekly feedback session during pilot."
- fail_example: Describes interface changes per phase but says nothing about rollout, training or adoption.

## RM-17: Compliance, security and controls
- weight: medium
- critical: false
- check: The roadmap addresses relevant regulatory, privacy, security and control
  requirements, including human oversight, auditability and escalation where
  automated or AI-driven decisions affect users or customers.
- pass_example: "All auto-approved invoices logged with rule applied; approvals above ₹5L always need a human; supplier bank data masked."
- fail_example: An automation or AI roadmap with no mention of data privacy, audit trail or human oversight.

## RM-18: Review and update cadence
- weight: low
- critical: false
- check: The roadmap states how often it is reviewed, who reviews it and how changes
  are communicated.
- pass_example: "Reviewed monthly at the Finance Ops steering committee; changes logged in revision history and shared in the monthly update."
- fail_example: No indication of when or how the roadmap will be revisited.

## RM-19: Outcome-focused, not only a feature list
- weight: medium
- critical: false
- check: Roadmap items are framed by the problem or outcome they address, not only as
  features or technical tasks, so each item's purpose is clear.
- pass_example: "Duplicate invoice detection – prevents double payments (est. ₹12L/year)."
- fail_example: "Build ML model v2", "Add API layer", "Dashboard 2.0" with no stated purpose.

## RM-20: Visual roadmap summary
- weight: low
- critical: false
- check: The roadmap includes a one-page visual summary (timeline, swimlanes or a
  phase-by-capability matrix) that matches the detailed sections.
- pass_example: A matrix of capabilities by phase plus a timeline bar chart, both consistent with the phase sections.
- fail_example: Text only, with no overview showing what lands when.

## RM-21: Completeness (no placeholders)
- weight: medium
- critical: false
- check: The document contains no unfinished content: no empty descriptions, "TBD",
  tentative wording left unresolved (e.g. "probable", "maybe") or headings without
  content. Open items are logged with an owner and date.
- pass_example: All sections populated; one open decision logged: "Chatbot channel – owner: Product Lead, due 15 Nov."
- fail_example: A data source listed with no description, and a key feature described as "probable".

## RM-22: Internal consistency
- weight: medium
- critical: false
- check: Phases, capabilities, systems, dates and terms are consistent across the
  summary, matrix, diagrams and detailed sections, and no statements contradict each
  other.
- pass_example: Every capability in the matrix appears in the matching phase section; systems in the diagram match the systems list.
- fail_example: The matrix says Phase 1 is embedded in the main tool, while the UX section says Phase 1 is a separate application; the diagram omits systems listed in the text.