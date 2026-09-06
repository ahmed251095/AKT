"""Shared build-up pricing logic for tender items and BOQ items.

The estimation office never types a selling rate. It enters what the item
actually costs -- the material (dry) cost and the operating cost of putting it
in place -- and the rate is built up from there:

    base      = dry_cost + operating_cost
    marked_up = base x (1 + profit% + contingency% + admin%)
    unit_rate = marked_up x (1 + expenses%)

Worked example from the pricing sheet: (2000 + 1000) x 1.40 x 1.14 = 4788.

The field declarations are repeated in the two concrete models on purpose:
both already own ``cost_rate``, ``unit_rate`` and ``currency_id`` from the base
module, and re-declaring those through an abstract mixin risks dropping the
attributes the base module set on them. Only the arithmetic is shared.
"""

PRICING_DEPENDS = (
    'dry_cost', 'operating_cost', 'profit_percent', 'contingency_percent',
    'admin_percent', 'expense_percent', 'use_pricing_formula', 'cost_rate',
    'is_section',
)


def compute_pricing(lines):
    """Fill the intermediate build-up figures on ``lines``."""
    for line in lines:
        if line.is_section:
            line.markup_percent = line.base_cost = line.markup_amount = 0.0
            line.price_before_expenses = line.expense_amount = 0.0
            continue
        markup = (line.profit_percent + line.contingency_percent
                  + line.admin_percent)
        base = (line.dry_cost + line.operating_cost
                if line.use_pricing_formula else line.cost_rate)
        marked_up = base * (1.0 + markup / 100.0)
        line.markup_percent = markup
        line.base_cost = base
        line.markup_amount = marked_up - base
        line.price_before_expenses = marked_up
        line.expense_amount = marked_up * (line.expense_percent / 100.0)


def compute_cost_rate(lines):
    """The cost rate is what the item costs us: dry cost plus operating cost."""
    for line in lines:
        if line.is_section or not line.use_pricing_formula:
            # Left as typed by the estimator for lump-sum items.
            continue
        line.cost_rate = line.dry_cost + line.operating_cost


def compute_unit_rate(lines):
    """The unit rate is the marked-up cost carrying the general expenses."""
    for line in lines:
        if line.is_section or not line.use_pricing_formula:
            continue
        line.unit_rate = line.price_before_expenses * (
            1.0 + line.expense_percent / 100.0)


def default_ratios(company):
    return {
        'profit_percent': company.construction_profit_percent,
        'contingency_percent': company.construction_contingency_percent,
        'admin_percent': company.construction_admin_percent,
        'expense_percent': company.construction_expense_percent,
    }


#: Fields carried over when a tender item becomes a BOQ item.
PRICING_COPY_FIELDS = (
    'use_pricing_formula', 'dry_cost', 'operating_cost', 'profit_percent',
    'contingency_percent', 'admin_percent', 'expense_percent',
)
