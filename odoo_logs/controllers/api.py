from odoo import http
from odoo.http import request


def create_event_ihub(summary, details, level="info"):
    request.env["ihub.event"].sudo().create(
        {
            "summary": summary,
            "level": level,
            "details": details,
        }
    )

class POSTController(http.Controller):

    @http.route(
        ["/api"],
        auth="public",
        methods=["POST"],
        csrf=False
    )
    def create_log(self, **kwargs):
        data = request.httprequest.data
        create_event_ihub(
            summary=f"{data[:30]}",
            details=data,
        )
        return "OK"