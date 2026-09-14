"""Shared build-up pricing logic for tender items and BOQ items.

The estimation office never types a selling rate. It enters what the item
actually costs -- the material (dry) cost and the operating cost of putting it
in place -- and the rate is built up from there:

    base      = dry_cost + operating_cost
    markup%   = profit% + contingency% + admin%   (overridable per item)
    marked_up = base x (1 + markup%)
    with_exp  = marked_up x (1 + expenses%)
    unit_rate = with_exp x (1 + tax%)

Worked example from the pricing sheet: (2000 + 1000) x 1.40 x 1.14 = 4788,
with no tax selected.

Tax comes last because the taxes a contractor prices in -- withholding, stamp
duty -- are deducted from the payment, so the rate has to be grossed up for
them to still net the intended price.

The field declarations are repeated in the two concrete models on purpose:
both already own ``cost_rate``, ``unit_rate`` and ``currency_id`` from the base
module, and re-declaring those through an abstract mixin risks dropping the
attributes the base module set on them. Only the arithmetic is shared.
"""

#: The markup follows the three ratios, until an estimator types over it.
MARKUP_DEPENDS = (
    'profit_percent', 'contingency_percent', 'admin_percent', 'is_section',
)

PRICING_DEPENDS = (
    'dry_cost', 'operating_cost', 'markup_percent', 'expense_percent',
    'use_pricing_formula', 'cost_rate', 'is_section', 'tax_percent',
)


def compute_markup(lines):
    """Add the three ratios up into the markup the rate is built on.

    The field is writable: an estimator who prices one item at a different
    markup types it in, and it stands until one of the three ratios moves.
    """
    for line in lines:
        line.markup_percent = 0.0 if line.is_section else (
            line.profit_percent + line.contingency_percent
            + line.admin_percent)


def compute_pricing(lines):
    """Fill the intermediate build-up figures on ``lines``."""
    for line in lines:
        if line.is_section:
            line.base_cost = line.markup_amount = 0.0
            line.price_before_expenses = line.expense_amount = 0.0
            line.price_before_tax = line.tax_amount = 0.0
            continue
        base = (line.dry_cost + line.operating_cost
                if line.use_pricing_formula else line.cost_rate)
        marked_up = base * (1.0 + line.markup_percent / 100.0)
        line.base_cost = base
        line.markup_amount = marked_up - base
        line.price_before_expenses = marked_up
        line.expense_amount = marked_up * (line.expense_percent / 100.0)
        with_expenses = marked_up + line.expense_amount
        line.price_before_tax = with_expenses
        line.tax_amount = with_expenses * (line.tax_percent / 100.0)


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
        line.unit_rate = line.price_before_tax * (
            1.0 + line.tax_percent / 100.0)


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

#: Copied separately: a many2many needs its own command.
PRICING_COPY_TAXES = 'tax_ids'
