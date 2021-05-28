from cachetools import cached, TTLCache
from odoo import api, fields, models


class Event(models.Model):
    """These events get listed in the ihub view."""

    _name = "ihub.event"
    _description = "Event"
    # _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "summary"

    level = fields.Selection(
        selection=[
            ("debug", "Debug"),
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
        ]
    )
    # Integration that called this (it's okay for this to be empty).
    integration_id = fields.Many2one(comodel_name="ihub.integration")

    # Summary of this event to display.
    summary = fields.Char()

    # Detailed information about this event. Should not be set for non errors or where not strictly necessary.
    details = fields.Text()

    # A related object, e.g. a created sales.order. Integrations need to extend this selection to include
    # models that need to be able to be displayed here.
    related = fields.Reference(
        selection=lambda self: self._get_related_models(), ondelete="set null"
    )

    @cached(cache=TTLCache(maxsize=1, ttl=30))
    def _get_related_models(self):
        event_selection = [
            (obj.model, obj.model) for obj in self.env["ir.model"].search([])
        ]
        return event_selection

    def search(self, *args, **kwargs):
        """Override search to fix events with broken relationships."""
        events = super().search(*args, **kwargs)
        if isinstance(events, models.Model):
            event_with_broken_related = [
                event
                for event in events
                if event.related and not event.related.exists()
            ]
            for event in event_with_broken_related:
                event.related = None
        return events
