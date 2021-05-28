# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Integration Hub",
    "version": "0.0.1",
    "category": "Tools",
    "summary": "Centralised logs and utilities for integrations.",
    "description": """
    Provides a centralised interface to see all logs and errors from different integrations. Meant to be used and 
    understood by normal non technical users.
    
    Uses the odoo connector module, creating listeners, so messages can be sent from any module for them to show up.
    Provides default error classes containing error messages, for standard actions, e.g. authentication issues or
    internal server errors.
    When developing an integration, log every transaction here and optionally also other actions, e.g. data validation,
    etc.. Any time data fails to be imported for any reason, or data is imported it should appear in this application.
    
    Displays job queue (ihub.queue) as well.
    """,
    "installable": True,
    "application": True,
    "external_dependencies": {"python": ["cachetools", "requests"]},
    "depends": ["mail"],
    "data": [
        "security/group.xml",
        "security/ir.model.access.csv",
        "views/ihub.xml",
        "views/events.xml",
        "views/queue.xml",
        "views/manual_wizard.xml",
        "views/integration.xml",
        "data/states.xml",
        "data/mail_template.xml",
        "views/integration_wizard.xml",
        "views/demo_integration.xml",
    ],
}
