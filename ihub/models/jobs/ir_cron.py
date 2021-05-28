from odoo import models, api, fields


class Cron(models.Model):
    _inherit = "ir.cron"

    # Optional reference to job
    ihub_integration_id = fields.Many2one(comodel_name="ihub.integration")
