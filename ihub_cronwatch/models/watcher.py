from odoo import models, fields, api


class Watcher(models.Model):
    """Watches one cron job."""

    _name = "ihub_cronwatch.watcher"
    _description = "Cron Watcher"
    _inherit = ["mail.thread"]

    cron = fields.Many2one(comodel_name="ir.cron")
    cron_active = fields.Boolean(default=True)

    @api.model
    def check(self):
        """Iterates over all watchers, checking if their jobs are still existing and active."""
        watchers = self.search([])
        template_ids = self.env["mail.template"].browse(
            self.env.ref("ihub_cronwatch.cronwatch_mail_template").ids
        )
        for watcher in watchers:
            if (not watcher.cron or not watcher.cron.active) and watcher.cron_active:
                watcher.cron_active = False
                mapped_email = {
                    "recipient_ids": watcher.message_partner_ids
                }
                try:
                    template_ids.send_mail(
                        watcher.id, email_values=mapped_email, force_send=True
                    )
                except BaseException as e:
                    self.ihub_error(
                        summary="Failed to send cronwatch notifications",
                        details=str(e)
                    )
            elif (watcher.cron and watcher.cron.active) and not watcher.cron_active:
                watcher.cron_active = True
