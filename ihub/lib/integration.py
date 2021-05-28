from odoo import fields, models, exceptions
from datetime import timedelta


class AbstractIntegration(models.AbstractModel):
    """Abstract integration class."""

    _name = "ihub.abstract_integration"
    _inherits = {"ihub.integration": "super_id"}
    _description = "Abstract Integration"

    super_id = fields.Many2one(
        comodel_name="ihub.integration", required=True, ondelete="cascade"
    )
    description = ""

    is_job = True
    is_manually_runnable = True
    delay = timedelta(minutes=1)
    has_time_period = True
    is_multi_company_compatible = False
    is_singleton = False

    def create(self, *args, **kwargs):
        """Raise an error if multiple instances of singleton integration are created."""
        if self.is_singleton:
            if self.env[self._name].search([]):
                raise exceptions.UserError("You can only create one instance of this integration.")

        return super().create(*args, **kwargs)

    def run_from_to(self, _from, _to):
        raise NotImplementedError

    def open_settings(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "views": [[False, "form"]],
            "res_id": self.id,
        }

    def fail(self):
        self.super_id.set_failed()
