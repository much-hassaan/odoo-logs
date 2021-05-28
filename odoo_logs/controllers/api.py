import base64
import datetime

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
        current_date_and_time = datetime.datetime.now()
        current_date_and_time_string = str(current_date_and_time)
        extension = ".txt"

        file_name = current_date_and_time_string + extension
        file = open(file_name, 'w')

        file.write(data) # Write Data


        datas = base64.encodebytes(file)
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'datas': datas,
            'datas_fname': file_name
        })

        create_event_ihub(
            summary=f"{file_name}",
            details=f"Wrote file {file_name}",
        )
        return "OK"