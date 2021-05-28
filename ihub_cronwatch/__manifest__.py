# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Integration Hub: Cron Watch",
    "version": "0.0.1",
    "category": "Tools",
    "summary": "Allows to supervise cron jobs from ihub",
    "description": """
    Adds a tab to ihub which allows to supervise (odoo) cron jobs and get notified if they are no longer active.
    """,
    "installable": True,
    "application": True,
    "depends": ["ihub"],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_template.xml",
        "data/watcher_job.xml",
        "views/watcher.xml",
    ],
}
