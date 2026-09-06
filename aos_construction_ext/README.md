# Construction Management — Business Extension

Extends `aos_construction_management` with the way the contractor actually
operates. Nothing in the base module is edited, so its updates stay safe to
apply.

## What it adds

### Build-up pricing
Tender and BOQ items are priced from cost, not from a typed rate:

```
base      = dry_cost + operating_cost
marked_up = base x (1 + profit% + contingency% + admin%)
unit_rate = marked_up x (1 + expenses%)
```

`(2000 + 1000) x 1.40 x 1.14 = 4788`

Defaults for the four ratios live on the company (Construction → Configuration →
Settings). An item can be taken off the formula with **Build-up Pricing** when it
is quoted as a lump sum.

### Tender lifecycle
`draft → pending_approval → in_progress → submitted → won / lost`

* Management approves opening the operation before any money is spent.
* The conditions booklet fee is only payable after that approval.
* A bid cannot be submitted while a required document is missing or expired, or
  while the bid bond is unissued.
* A lost tender waits in `bond_pending` until finance confirms the bond came
  back, then closes.

### Bonds
Bid bond on the tender, performance bond on the project: amount, ratio,
instrument, bank, issue and expiry dates, and the release cycle.

### Document checklists
Configurable document types split across technical, financial and legal files,
pulled onto a tender or project with one button, with expiry tracking.

### Project execution
Team roles for electrical, mechanical, logistics, finance, accountant and HR
supervisor; site warehouse and location; a Drive folder link; a hold that needs
a reason; and a handover step before closure.

### Analysis
Quantity variance against the BOQ on every item, and a profit statement
splitting cost into materials, wages, equipment, subcontractors, overheads,
certified subcontractor work and direct purchases.

### Output
Excel pricing sheet and a PDF cover letter on the tender, PDF profit statement
on the project.

## Install notes

Existing tender and BOQ items are switched off the formula by the post-install
hook and keep their current rates, so nothing already priced changes value.

Departments are shipped as six groups (management, technical office, execution,
finance, warehouses, HR & purchasing). Assign them alongside the base
User/Manager groups.
