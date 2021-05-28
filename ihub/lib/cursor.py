import contextlib
from odoo import registry, api


@contextlib.contextmanager
def new_environment(obj):
    """New environment with new cursor. Any changes in this context will be committed."""
    with registry(obj.env.cr.dbname).cursor() as cursor:
        yield api.Environment(cursor, obj.env.uid, {})
        cursor.commit()
