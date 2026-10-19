# Business Requirements Document: Accounts Payable Invoice Automation

## Document Control

| Field | Value |
|---|---|
| Document title | Accounts Payable Invoice Automation BRD |
| Version | 1.2 |
| Author | Jordan Patel, Senior Business Analyst |
| Date | 14 March 2026 |
| Status | Approved |

### Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 20 Feb 2026 | J. Patel | First draft |
| 1.1 | 3 Mar 2026 | J. Patel | Added KPIs and risks after stakeholder workshop |
| 1.2 | 14 Mar 2026 | J. Patel | Final updates from Finance review |

## 1. Executive Summary and Business Context

The Accounts Payable (AP) team processes around 6,500 supplier invoices per month. Invoices arrive as PDF email attachments and are keyed manually into the ERP. Four full-time AP clerks spend roughly 60% of their time on data entry. In 2025, 7% of invoices contained keying errors, and 11% of invoices were paid late, costing an estimated £85,000 in late-payment penalties and lost early-payment discounts.

This project will automate invoice capture and purchase-order matching so that AP clerks focus on exceptions rather than data entry.

## 2. Current State and Business Problem

Today, invoices are received in a shared mailbox. A clerk opens each PDF, types the header and line details into the ERP, and manually looks up the matching purchase order (PO). Invoices with discrepancies are emailed to the buyer, and there is no tracking of how long they wait. The average cycle time from receipt to approval is 9 business days. Month-end close is regularly delayed by 1 to 2 days because of unprocessed invoices.

## 3. Business Objectives

- OBJ-1: Reduce average invoice cycle time from 9 business days to 3 business days within 6 months of go-live.
- OBJ-2: Reduce invoice processing cost by 20% within 12 months of go-live (baseline: £4.10 per invoice).
- OBJ-3: Reduce invoice keying errors from 7% to below 1% within 6 months of go-live.

## 4. Scope

### 4.1 In Scope

- Supplier invoices in GBP and EUR received by email.
- Automated capture of invoice header and line data.
- Automatic matching of invoices to purchase orders.
- An exceptions queue for unmatched or disputed invoices.

### 4.2 Out of Scope

- Employee expense claims.
- Invoices received on paper by post (fewer than 2% of volume).
- Historical invoices received before 1 January 2024.
- Changes to the supplier payment run process.

## 5. Stakeholders

| Stakeholder | Role | Responsibility (RACI) |
|---|---|---|
| Head of Finance Operations | Sponsor | Accountable: approves scope and budget |
| AP Team Lead | Business owner | Responsible: requirements sign-off and UAT lead |
| AP Clerks (4) | End users | Consulted: requirements workshops and UAT testers |
| Procurement Buyers | Resolve PO discrepancies | Informed: new exceptions process |
| IT Delivery Lead | Delivery | Responsible: solution delivery |

## 6. Business Requirements

| ID | Requirement | Priority |
|---|---|---|
| BR-01 | AP clerks must be able to see every invoice received by email in one list within 15 minutes of receipt. | Must |
| BR-02 | Invoice header data (supplier, invoice number, date, amount, currency, PO number) must be captured without manual keying for at least 85% of invoices. | Must |
| BR-03 | Invoices must be matched automatically to a PO when supplier, PO number and total amount agree within a tolerance of £5. | Must |
| BR-04 | Invoices that cannot be matched must be routed to an exceptions queue with the reason shown. | Must |
| BR-05 | Approvers must be able to approve or reject an invoice within 2 business days of it entering their queue, and receive a reminder after 1 business day. | Should |
| BR-06 | Invoices over £10,000 must be approved by a second approver from Finance. | Must |
| BR-07 | AP managers must be able to see the number and age of invoices in each queue at any time. | Should |
| BR-08 | Duplicate invoices (same supplier, invoice number and amount) must be flagged before approval. | Must |
| BR-09 | Suppliers should receive an automatic email when their invoice is approved for payment. | Could |

## 7. Assumptions, Constraints and Dependencies

- Assumption: at least 95% of invoices continue to arrive as text-based PDF attachments.
- Assumption: PO data in the ERP is accurate and up to date.
- Constraint: the solution must be live before the financial year-end on 31 March 2027.
- Constraint: total project budget is £180,000.
- Constraint: invoice data must be stored in the UK for GDPR compliance.
- Dependency: the ERP upgrade (Project Atlas) must complete by Q4 2026 to provide the PO matching interface.

## 8. Risks and Mitigations

| Risk | Mitigation | Owner |
|---|---|---|
| Supplier data quality in the ERP is poor, reducing match rates | Data cleansing sprint before go-live | AP Team Lead |
| AP clerks resist the new process | Involve clerks in UAT; run training before go-live | Head of Finance Ops |
| Project Atlas is delayed | Phase the rollout: capture first, matching once Atlas is live | IT Delivery Lead |

## 9. Success Metrics and KPIs

| KPI | Baseline | Target | How measured |
|---|---|---|---|
| Average invoice cycle time | 9 business days | 3 business days | Monthly AP dashboard |
| Cost per invoice | £4.10 | £3.28 | Quarterly Finance cost report |
| Keying error rate | 7% | Below 1% | Monthly audit sample of 100 invoices |
| Late payments | 11% | Below 3% | Monthly ERP payment report |

## 10. Approval and Sign-off

| Name | Role | Decision | Date |
|---|---|---|---|
| Sarah Mitchell | Head of Finance Operations | Approved | 14 Mar 2026 |
| David Owusu | AP Team Lead | Approved | 14 Mar 2026 |
| Priya Nair | IT Delivery Lead | Approved | 15 Mar 2026 |
