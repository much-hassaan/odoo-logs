from odoo import models, fields


class State(models.Model):
    _name = "ihub.state"
    _description = "IHub integration state"

    name = fields.Char()
