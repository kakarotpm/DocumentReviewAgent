---
doc_type: roadmap
display_name: Product / Project Roadmap
pass_threshold: 80
description: Sets out the vision, initiatives, timeline and milestones for a product or project.
---

## RDM-01: Version, owner and last-updated date
- weight: low
- critical: false
- check: The roadmap shows its version, owner and the date it was last updated.
- pass_example: "Roadmap v3, owned by Head of Product, last updated 1 Oct 2026."
- fail_example: No version, owner or date.

## RDM-02: Vision and strategic objectives
- weight: high
- critical: false
- check: The roadmap states the vision and the strategic objectives it serves, clearly
  enough that a reader understands what success looks like.
- pass_example: "Vision: suppliers onboard themselves in a day. Objectives: cut onboarding cost 50%; zero duplicate payments by FY27."
- fail_example: A list of features with no stated vision or objectives.

## RDM-03: Time horizon and phases
- weight: medium
- critical: false
- check: The roadmap covers a defined time horizon broken into phases, quarters or similar
  periods.
- pass_example: "FY27 roadmap: Q1 Foundations, Q2 Pilot, Q3–Q4 Scale."
- fail_example: Items listed with no time periods.

## RDM-04: Initiatives linked to objectives
- weight: high
- critical: true
- check: Every initiative is linked to at least one strategic objective. Some initiatives
  unlinked is partially met.
- pass_example: "Supplier portal (Q2) → Objective 1: cut onboarding cost 50%."
- fail_example: Initiatives listed with no connection to any objective.

## RDM-05: Milestones with dates
- weight: high
- critical: true
- check: Key milestones are listed with target dates (a specific date or at least a month).
  Milestones with only vague timing ("later", "phase 2") are partially met.
- pass_example: "Pilot go-live: 15 Feb 2027. Full rollout: 30 Jun 2027."
- fail_example: "Go-live: TBC."

## RDM-06: Owner per initiative
- weight: medium
- critical: false
- check: Each initiative has a named owner (person or role).
- pass_example: "Supplier portal: owner Priya S. (Product Manager)."
- fail_example: No owners shown.

## RDM-07: Dependencies between initiatives
- weight: medium
- critical: false
- check: Dependencies between initiatives, and on external teams or systems, are shown.
- pass_example: "Supplier portal depends on SAP API upgrade (IT Platform team, Q1)."
- fail_example: No dependencies mentioned.

## RDM-08: Assumptions and resource needs
- weight: medium
- critical: false
- check: Key assumptions and the resources needed (people, budget, tools) are stated.
- pass_example: "Assumes 2 developers from Q2; budget £120k approved for FY27."
- fail_example: No assumptions or resources mentioned.

## RDM-09: Risks
- weight: low
- critical: false
- check: The main risks to the roadmap are identified, ideally with a mitigation.
- pass_example: "Risk: SAP upgrade slips. Mitigation: portal can launch with manual vendor creation."
- fail_example: No risks mentioned.

## RDM-10: Success measures per phase
- weight: medium
- critical: false
- check: Each phase has success measures that show whether it achieved what it set out to.
- pass_example: "Pilot success: 50 suppliers onboarded via portal with average cycle time under 3 days."
- fail_example: No measures of success for any phase.
