# Construction Management 19.0.3.0.0

## Integrated construction control backbone

This release separates and connects the three core construction concepts:

- **WBS Phase**: project breakdown and cost-control level.
- **BOQ Item**: contractual quantity, budget revenue and budget cost.
- **Work Order**: site execution instruction and accepted quantities.

## Main additions

- BOQ budget cost rate, revenue, margin and progress indicators.
- BOQ links to WBS, execution, material requisitions, purchase lines and certificates.
- Work order execution lines with planned, executed, accepted and rejected quantities.
- Material requisition lines linked to BOQ items and WBS phases.
- RFQ/PO lines automatically inherit project, WBS, BOQ item and work order.
- Customer and subcontractor certificate lines linked to BOQ/WBS/work order.
- Previous and remaining certificate quantities are calculated from certified records.
- Invoice/vendor bill lines inherit WBS, BOQ and work-order references.
- WBS cost-control figures: budget revenue, budget cost, committed cost, certified revenue, subcontract certified cost and forecast margin.

## Upgrade

Update the Apps list, then upgrade **Construction Management**. Use a staging database first.
