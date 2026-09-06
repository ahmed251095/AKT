import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Leave already-priced items exactly as they are.

    ``unit_rate`` and ``cost_rate`` become computed by this module. Items that
    were priced before it was installed carry rates that nobody entered a cost
    breakdown for, so they are switched off the formula and their existing cost
    rate is kept as the dry cost. Nothing changes value, and the estimator can
    switch a line onto the formula the next time the item is revisited.
    """
    for model in ('construction.tender.line', 'construction.boq.line'):
        lines = env[model].search([])
        if not lines:
            continue
        for line in lines:
            line.write({
                'use_pricing_formula': False,
                'dry_cost': line.cost_rate,
            })
        _logger.info(
            'aos_construction_ext: kept %s existing %s rate(s) untouched.',
            len(lines), model)
