from odoo import models, fields, api


class IntegrationWizard(models.TransientModel):
    _name = "ihub.integration_wizard"
    _description = "Integration Wizard"

    name = fields.Char()
    model = fields.Selection(selection="_compute_models")
    description = fields.Char(compute="_compute_fields")

    @api.model
    def _compute_models(self):
        # finds all direct subclasses of AbstractIntegration and gets their ir_model instances.
        integration_models = self.env["ir.model"].search([("model", "like", ".integration")])
        integration_models = filter(lambda m: m.model not in ["ihub.integration_wizard", "ihub.integration"], integration_models)
        return [(model.model, model.name) for model in integration_models]

    @api.onchange("model")
    @api.model
    def _compute_fields(self):
        integration_models = self._compute_models()
        if self.model:
            self.description = self.env[self.model].description
            if not self.name or self.name in [model[1] for model in integration_models]:
                self.name = [
                    model[1] for model in integration_models if model[0] == self.model
                ][0]
        else:
            self.description = ""

    def create_integration(self):
        new_integration = self.env[self.model].create(dict(name=self.name))
        return {
            "type": "ir.actions.act_window",
            "res_model": "ihub.integration",
            "views": [[False, "form"]],
            "res_id": new_integration.super_id.id,
        }
