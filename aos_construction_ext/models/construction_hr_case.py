from odoo import fields, models


class ConstructionHrCase(models.Model):
    """Anything the HR supervisor has to follow up on a site.

    Appraisals, absences and disputes are what the site supervisor reports back
    to the office, and they belong to the project so their cost and their effect
    on progress stay visible next to it.
    """
    _name = 'construction.hr.case'
    _description = 'Construction HR Case'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Subject', required=True, tracking=True)
    project_id = fields.Many2one(
        'construction.project', string='Project', required=True, index=True,
        ondelete='cascade', tracking=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', tracking=True)
    case_type = fields.Selection(
        [('appraisal', 'Appraisal'),
         ('issue', 'Issue'),
         ('absence', 'Absence'),
         ('warning', 'Warning'),
         ('request', 'Request'),
         ('other', 'Other')],
        string='Type', required=True, default='issue', tracking=True)
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)
    reported_by = fields.Many2one(
        'res.users', string='Reported By', default=lambda self: self.env.user)
    rating = fields.Selection(
        [('1', 'Poor'), ('2', 'Below Expectations'), ('3', 'Meets'),
         ('4', 'Exceeds'), ('5', 'Outstanding')],
        string='Rating',
        help='Filled in for appraisals.')
    description = fields.Text(string='Description')
    resolution = fields.Text(string='Resolution')
    state = fields.Selection(
        [('open', 'Open'), ('in_progress', 'In Progress'),
         ('done', 'Closed'), ('cancelled', 'Cancelled')],
        string='Status', default='open', required=True, tracking=True)

    def action_start(self):
        self.write({'state': 'in_progress'})
        return True

    def action_close(self):
        self.write({'state': 'done'})
        return True

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        return True

    def action_reset(self):
        self.write({'state': 'open'})
        return True
