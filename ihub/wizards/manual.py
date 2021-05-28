from odoo import models, fields, api
from datetime import datetime, timedelta


class ManualWizard(models.TransientModel):
    _name = "ihub.manual_wizard"
    _description = "Wizard for manually running Integrations"

    from_date = fields.Datetime(
        default=lambda self: self.now_in_timezone(hour=0, minute=0, second=0)
        - timedelta(days=1)
    )
    to_date = fields.Datetime(
        default=lambda self: self.now_in_timezone(hour=0, minute=0, second=0)
    )

    has_time_period = fields.Boolean(
        default=lambda self: self.integration_has_time_period()
    )

    def integration_has_time_period(self):
        integration = self._get_integration_from_context()
        if integration:
            return integration.sub_has_time_period
        else:
            return False

    def now_in_timezone(self, **kwargs):
        """Calculates the current user time, with time fields replaced by values in kwargs."""
        tz = self.to_tz(self.env.user.tz_offset)
        return datetime.now().replace(**kwargs) - timedelta(hours=tz)

    def run(self):
        integration = self._get_integration_from_context()
        integration.with_context(ihub_manual=True).sudo().run_manual_job(
            self.from_date, self.to_date
        )

    def _get_integration_from_context(self):
        context = self.env.context
        active_model = context.get("active_model")
        if active_model:
            return self.env[active_model].browse(context.get("active_id"))
        return None

    @staticmethod
    def to_tz(tz_str):
        """
        Convert odoo timezone offset from str to float
        :param tz_str: tz offset string
        """
        try:
            if tz_str and len(tz_str) == 5:
                return int(tz_str) / 100
        except ValueError:
            return None
        return None
