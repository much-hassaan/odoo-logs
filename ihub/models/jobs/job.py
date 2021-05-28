from odoo import models, fields, api
from psycopg2.extensions import TransactionRollbackError
import time


class IntegrationJob(models.Model):
    """Facade for easier use of cron jobs."""

    _name = "ihub.job"
    _description = "Integration Hub Job"

    integration_id = fields.Many2one(comodel_name="ihub.integration")
    name = fields.Char()

    function = fields.Char()
    from_date = fields.Datetime()
    to_date = fields.Datetime()
    state = fields.Selection(
        selection=[
            ["pending", "Pending"],
            ["failed", "Failed"],
            ["done", "Done"],
            ["running", "Running"],
        ]
    )

    def create(self, vals):
        """Create a cron job"""
        vals["state"] = "pending"
        return super().create(vals)

    @api.model
    def fail(self):
        for res in self:
            res.state = "failed"

    @api.model
    def done(self):
        for res in self:
            res.state = "done"
