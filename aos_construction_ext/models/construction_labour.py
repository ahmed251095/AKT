from odoo import api, fields, models


class ConstructionLabourType(models.Model):
    """A trade the site works in shifts: mason, steel fixer, driver, foreman."""
    _name = 'construction.labour.type'
    _description = 'Labour Type'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    default_shift_rate = fields.Monetary(
        string='Default Shift Rate', currency_field='currency_id',
        help='What one person of this trade costs for one shift.')
    default_hours = fields.Float(string='Hours per Shift', default=8.0)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id)
    note = fields.Text(string='Notes')


class ConstructionLabourLine(models.Model):
    """How many crews, for how many shifts, at what cost.

    The estimating office prices execution into every item, but nobody checks
    that the crews needed to do the work in the time allowed actually fit
    inside that money. This is the estimate, next to the figure it has to fit.
    """
    _name = 'construction.labour.line'
    _description = 'Labour Requirement'
    _order = 'sequence, id'

    tender_id = fields.Many2one(
        'construction.tender', string='Tender', ondelete='cascade', index=True)
    project_id = fields.Many2one(
        'construction.project', string='Project', ondelete='cascade',
        index=True)
    sequence = fields.Integer(string='Sequence', default=10)

    labour_type_id = fields.Many2one(
        'construction.labour.type', string='Trade', required=True)
    boq_line_id = fields.Many2one(
        'construction.boq.line', string='BOQ Item',
        help='Leave empty for crews that serve the whole site.')
    wbs_id = fields.Many2one('construction.wbs', string='WBS Phase')

    crew_size = fields.Integer(
        string='Crew Size', default=1, required=True,
        help='People of this trade working one shift.')
    shift_count = fields.Integer(
        string='Shifts', default=1, required=True,
        help='How many shifts this crew is needed for.')
    hours_per_shift = fields.Float(
        string='Hours per Shift', compute='_compute_from_type', store=True,
        readonly=False)
    shift_rate = fields.Monetary(
        string='Rate per Person / Shift', compute='_compute_from_type',
        store=True, readonly=False)

    man_shifts = fields.Integer(
        string='Man-shifts', compute='_compute_totals', store=True,
        help='Crew size times shifts: the labour the estimate commits to.')
    total_hours = fields.Float(
        string='Total Hours', compute='_compute_totals', store=True)
    total_cost = fields.Monetary(
        string='Estimated Cost', compute='_compute_totals', store=True)

    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id)
    note = fields.Char(string='Notes')

    @api.depends('labour_type_id')
    def _compute_from_type(self):
        for line in self:
            if not line.labour_type_id:
                continue
            line.hours_per_shift = line.labour_type_id.default_hours
            line.shift_rate = line.labour_type_id.default_shift_rate

    @api.depends('crew_size', 'shift_count', 'hours_per_shift', 'shift_rate')
    def _compute_totals(self):
        for line in self:
            line.man_shifts = line.crew_size * line.shift_count
            line.total_hours = line.man_shifts * line.hours_per_shift
            line.total_cost = line.man_shifts * line.shift_rate

    @api.depends('labour_type_id', 'crew_size', 'shift_count')
    def _compute_display_name(self):
        for line in self:
            trade = line.labour_type_id.name or ''
            line.display_name = '%s (%s x %s)' % (
                trade, line.crew_size, line.shift_count)
