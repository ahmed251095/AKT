"""Shared pricing logic for tender items and BOQ items.

Two conventions are in use in the trade, and an item carries the one it was
priced under.

``buildup`` -- the rate is built up from the cost by markups:

    base      = dry_cost + operating_cost
    markup%   = profit% + contingency% + admin%   (overridable per item)
    marked_up = base x (1 + markup%)
    with_exp  = marked_up x (1 + expenses%)
    unit_rate = with_exp x (1 + tax%)

Worked example from the pricing handbook: (2000 + 1000) x 1.40 x 1.14 = 4788,
with no tax selected.

``margin`` -- every ratio is a share *of the selling price* rather than an
addition to the cost, so the rate is what the cost has to be grossed up to for
all the shares to come out of it and still leave the cost covered:

    shares%   = authority% + admin% + contingency% + profit% + expenses% + tax%
    unit_rate = base / (1 - shares%)

Worked example from the estimation sheet: 80.5 / (1 - 0.65) = 230. This is the
convention the office's own spreadsheets are written in, and the one the Excel
import reads.

``manual`` -- the cost rate and the selling rate are both typed. Lump-sum work,
and any item whose figures came from somewhere other than a breakdown.

Tax comes last in the build-up because the taxes a contractor prices in --
withholding, stamp duty -- are deducted from the payment, so the rate has to be
grossed up for them to still net the intended price. Under ``margin`` the tax
is simply one more share of the rate, which is the same reading.

The field declarations are repeated in the two concrete models on purpose:
both already own ``cost_rate``, ``unit_rate`` and ``currency_id`` from the base
module, and re-declaring those through an abstract mixin risks dropping the
attributes the base module set on them. Only the arithmetic is shared.
"""

#: How an item's selling rate is arrived at.
PRICING_METHODS = [
    ('buildup', 'Build-up on Cost'),
    ('margin', 'Share of Selling Price'),
    ('manual', 'Typed by Hand'),
]

#: The ratios that make up the selling price under the ``margin`` method.
MARGIN_RATIOS = (
    'authority_percent', 'admin_percent', 'contingency_percent',
    'profit_percent', 'expense_percent', 'tax_percent',
)

#: The markup follows the three ratios, until an estimator types over it.
MARKUP_DEPENDS = (
    'profit_percent', 'contingency_percent', 'admin_percent', 'is_section',
)

PRICING_DEPENDS = (
    'dry_cost', 'operating_cost', 'markup_percent', 'pricing_method',
    'cost_rate', 'is_section',
) + MARGIN_RATIOS

COST_RATE_DEPENDS = (
    'dry_cost', 'operating_cost', 'pricing_method', 'is_section',
)

UNIT_RATE_DEPENDS = (
    'price_before_tax', 'base_cost', 'pricing_method', 'is_section',
) + MARGIN_RATIOS


def shares(line):
    """The part of the selling rate that is spoken for, as a fraction."""
    return sum(getattr(line, ratio) for ratio in MARGIN_RATIOS) / 100.0


def margin_rate(line):
    """The selling rate the shares have to be taken out of.

    Shares adding up to the whole rate - or more - leave nothing for the cost
    and no rate to solve for; the constraint on the models refuses to store
    that, and zero is what is shown while it is being typed.
    """
    taken = shares(line)
    return line.base_cost / (1.0 - taken) if taken < 1.0 else 0.0


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
    """Fill the intermediate figures the rate is read through."""
    for line in lines:
        if line.is_section:
            line.base_cost = line.markup_amount = 0.0
            line.price_before_expenses = line.expense_amount = 0.0
            line.price_before_tax = line.tax_amount = 0.0
            line.authority_amount = 0.0
            continue

        if line.pricing_method == 'margin':
            line.base_cost = line.dry_cost + line.operating_cost
            rate = margin_rate(line)
            # Each ratio is a slice of the rate, so the figures are read back
            # off the rate rather than added onto the cost.
            line.tax_amount = rate * line.tax_percent / 100.0
            line.expense_amount = rate * line.expense_percent / 100.0
            line.authority_amount = rate * line.authority_percent / 100.0
            line.price_before_tax = rate - line.tax_amount
            line.price_before_expenses = (
                line.price_before_tax - line.expense_amount)
            line.markup_amount = (line.price_before_expenses
                                  - line.base_cost - line.authority_amount)
            continue

        base = (line.dry_cost + line.operating_cost
                if line.pricing_method == 'buildup' else line.cost_rate)
        marked_up = base * (1.0 + line.markup_percent / 100.0)
        line.base_cost = base
        line.markup_amount = marked_up - base
        line.price_before_expenses = marked_up
        line.expense_amount = marked_up * (line.expense_percent / 100.0)
        with_expenses = marked_up + line.expense_amount
        line.price_before_tax = with_expenses
        line.tax_amount = with_expenses * (line.tax_percent / 100.0)
        # The authority share belongs to the sheet convention only; under a
        # build-up there is no slice of the rate for it to be.
        line.authority_amount = 0.0


def compute_cost_rate(lines):
    """The cost rate is what the item costs us: dry cost plus operating cost."""
    for line in lines:
        if line.is_section or line.pricing_method == 'manual':
            # Left as typed by the estimator for lump-sum items.
            continue
        line.cost_rate = line.dry_cost + line.operating_cost


def compute_unit_rate(lines):
    """The selling rate, by whichever convention the item is priced under."""
    for line in lines:
        if line.is_section or line.pricing_method == 'manual':
            continue
        if line.pricing_method == 'margin':
            line.unit_rate = margin_rate(line)
            continue
        line.unit_rate = line.price_before_tax * (
            1.0 + line.tax_percent / 100.0)


def default_ratios(company):
    return {
        'profit_percent': company.construction_profit_percent,
        'contingency_percent': company.construction_contingency_percent,
        'admin_percent': company.construction_admin_percent,
        'expense_percent': company.construction_expense_percent,
        'authority_percent': company.construction_authority_percent,
    }


#: Set on the recordset while pricing is copied from one document to another,
#: so the inverses that switch a typed-over item to hand pricing stand down.
#: A copy is not someone typing a rate: the pricing mode travels with it.
KEEP_PRICING_MODE = 'construction_pricing_copy'


#: Fields carried over when a tender item becomes a BOQ item.
PRICING_COPY_FIELDS = (
    'pricing_method', 'dry_cost', 'operating_cost', 'profit_percent',
    'contingency_percent', 'admin_percent', 'expense_percent',
    'authority_percent',
)

#: Copied separately: a many2many needs its own command.
PRICING_COPY_TAXES = 'tax_ids'
