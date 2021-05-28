# Integration Hub

The integration hub (ihub) provides a common user interface for our integrations, as well as an interface for managing the state of integrations and starting jobs on regular time frames. It is meant to be used by non-technical users.

## Integrations

###Integrations
_(See ihub.integration.demo for an example)_  
When creating a new integration, create a model which inherits from `AbstractIntegration`.
Copy this example and set:
* `_name` to something with `.integration` in it
* `run_from_to` to run your integration
* `open_settings` to display your integration settings

```python
from odoo import exceptions, api, models, fields
from odoo.addons.ihub.lib.integration import AbstractIntegration
from datetime import datetime, timedelta

class DemoIntegration(models.Model):
    """Example integration implementation"""

    _name = "ihub.integration.demo"
    _inherit = "ihub.abstract_integration"
    _description = "Demo Integration"

    # If this is True, the from/to date is shown and clicking on start starts a cron job
    is_job = True

    # If this is True, the run manually button is shown
    is_manually_runnable = True

    # If this is True, a time period can be selected in run manually
    has_time_period = True

    # If this is True, the integration handles multi company behaviour by itself
    # If this is False, a selection is displayed for the company in which to run this integration
    is_multi_company_compatible = False

    # If this is True, it's possible to create only one instance of this integration
    is_singleton = False

    # This defines the minimum delay between _to (in run_from_to) and the cron job actually running.
    delay = timedelta(seconds=10)

    fail_run = fields.Boolean(default=False)

    description = (
        "<div>A <b>demo</b> integration, without functionality. "
        "It's only good at demonstrating how this works.</div>"
    )
    a_custom_fields = fields.Char(string="Custom Field")

    # This method is called by RUN MANUALLY and the job started by START
    @api.model
    def run_from_to(self, _from: datetime, _to: datetime):
        msg=f"Integration just for demonstration. run_from_to called with {_from} {_to}"
        self.ihub_warning(
            summary=msg,
            details="",
            related=None,
            integration=self,
        )

    # This view is returned when INTEGRATION SETTINGS is clicked
    @api.model
    def open_settings(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "ihub.integration.demo",
            "views": [[False, "form"]],
            "res_id": self.id,
        }
``` 

As well as a view for its settings:

```xml
<odoo>
    <data>
        <record id="integration_demo_view" model="ir.ui.view">
            <field name="name">ihub.integration.demo.form</field>
            <field name="model">ihub.integration.demo</field>
            <field name="arch" type="xml">
                <form string="Integration Demo">
                    <sheet>
                        <group>
                            <field name="name"/>
                            <field name="a_custom_field"/>
                        </group>
                        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse ac porta erat, sit amet dignissim turpis. Aenean ultrices diam eget ex fermentum, ac fringilla urna pulvinar.
                    </sheet>
                </form>
            </field>
        </record>
    </data>
</odoo>

```
## Failing
Call `self.fail()` to put your integration into a failed state.
If you'd like to raise an exception, use:
`self.ihub_error(..., raise=True)` (see below). This will lead t


## Events
In any class inheriting from `models.Model` call 

* `self.ihub_info(summary=None, details=None, related=None, integration=None)`
* `self.ihub_warning(summary=None, details=None, related=None, integration=None)`
* `self.ihub_error(summary=None, details=None, related=None, integration=None, raise=False)`

Where:

* `summary` is the title of the event
* `details` is detailed information, e.g. a json of transmitted data
* `related` is any object that is related to the event. An odoo object is expected (not just an id).
* `integration` is an instance of an integration
