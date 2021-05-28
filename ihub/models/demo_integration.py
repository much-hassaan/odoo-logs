import logging
from datetime import datetime, timedelta

from odoo import api, models, fields

from ..lib.integration import AbstractIntegration

LOGGER = logging.getLogger(__name__)


class DemoIntegration(models.Model):
    """Example integration implementation"""

    _name = "ihub.integration.demo"
    _inherit = "ihub.abstract_integration"
    _description = "Demo Integration"

    # If this is True, the from/to date is shown and clicking on start starts a cron job
    is_job = True

    # If this is True, the run manually button is shown
    is_manually_runnable = True

    # If this is True, a time period can be selected in run manually
    has_time_period = True

    # If this is True, the integration handles multi company behaviour by itself
    # If this is False, a selection is displayed for the company in which to run this integration
    is_multi_company_compatible = False

    # If this is True, it's possible to create only one instance of this integration
    is_singleton = False

    # This defines the minimum delay between _to (in run_from_to) and the cron job actually running.
    delay = timedelta(seconds=10)

    fail_run = fields.Boolean(default=False)

    description = (
        "<div>A <b>demo</b> integration, without functionality. "
        "It's only good at demonstrating how this works.</div>"
    )
    a_custom_fields = fields.Char(string="Custom Field")

    @api.model
    def run_from_to(self, _from: datetime, _to: datetime):
        if self.fail_run:
            raise self.ihub_error(
                f"Failed on purpose, run_from_to called with {_from} {_to}", raised=True
            )

        msg = (
            f"Integration just for demonstration. run_from_to called with {_from} {_to}"
        )
        self.ihub_warning(
            summary=msg, details="", related=None, integration=self,
        )

    @api.model
    def open_settings(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "ihub.integration.demo",
            "views": [[False, "form"]],
            "res_id": self.id,
        }
