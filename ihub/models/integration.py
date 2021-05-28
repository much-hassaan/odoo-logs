import traceback
from contextlib import contextmanager
from datetime import datetime, timedelta

from odoo import api
from odoo import models, fields, exceptions

from ..lib.cursor import new_environment
from ..lib.sub import sub
from ..lib.exceptions import IHubInterruptException


class Integration(models.Model):
    """Contains settings for an integration instance."""

    _name = "ihub.integration"
    _description = "Integration"
    _inherit = ["mail.thread"]

    _rec_name = "name"

    name = fields.Char()

    # Jobs are executed with this company
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    sub_id: fields.Reference = fields.Reference(
        selection="compute_children", ondelete="cascade"
    )
    status_name = fields.Char(compute="compute_status_name")

    # This cron job just the jobs
    cron_id = fields.Many2one("ir.cron")

    # Currently pending job
    job_id = fields.Many2one("ihub.job")

    # base url of service
    base_url = fields.Char()

    @api.model
    def _is_job(self):
        for res in self:
            res.compute_sub_id()
            res.sub_is_job = res.sub_id.is_job

    @api.model
    def _is_runnable(self):
        for res in self:
            res.compute_sub_id()
            res.sub_is_manually_runnable = res.sub_id.is_manually_runnable

    @api.model
    def _has_time_period(self):
        for res in self:
            res.compute_sub_id()
            res.sub_has_time_period = res.sub_id.has_time_period

    @api.model
    def _is_multi_company_compatible(self):
        for res in self:
            res.compute_sub_id()
            res.sub_is_multi_company_compatible = res.sub_id.is_multi_company_compatible

    # whether this is a job that's run regularily
    sub_is_job = fields.Boolean(compute="_is_job")
    sub_is_manually_runnable = fields.Boolean(compute="_is_runnable")
    sub_has_time_period = fields.Boolean(compute="_has_time_period")
    sub_is_multi_company_compatible = fields.Boolean(
        compute="_is_multi_company_compatible"
    )

    # -- job fields --
    job_next_run = fields.Datetime(string="Interval start")
    job_interval_scalar = fields.Integer(default=1)
    job_interval_unit = fields.Selection(
        selection=[("minutes", "Minutes"), ("hours", "Hours"), ("days", "Days")],
        default="days",
    )
    job_last_run = fields.Datetime(string="Interval stop")

    cron_next_run = fields.Datetime(string="Next run", related='cron_id.nextcall', readonly=True, help="This time is set by the integration, based on the optimal delay between the last date to be imported and the execution date. You cannot set this.")

    # List of importers
    # connectors = fields.Many2many(comodel_name="ihub.connector")
    state = fields.Selection([])
    status = fields.Many2one(
        comodel_name="ihub.state",
        default=lambda self: self.get_status("Created"),
        group_expand="_expand_stages",
    )

    def _expand_stages(self, *_, **__):
        """Returns stages that are displayed in the kanban view."""
        stage_ids = self.env["ihub.state"].search([])
        return stage_ids

    def create(self, vals_list):
        """Disables creation message ('Integration created')."""
        return super(Integration, self.with_context(mail_create_nolog=True)).create(
            vals_list
        )

    @sub
    def run_from_to(self, _from: datetime, _to: datetime):
        pass

    @sub
    def run(self):
        pass

    @sub
    def open_settings(self):
        pass

    @api.model
    def set_status(self, name):
        """Sets this integration to the state with the given name."""
        for res in self:
            res.status = res.get_status(name)

    def get_status(self, name):
        """Gets the ihub.state with the given name."""
        status = self.env["ihub.state"].search([["name", "=", name]])
        if not status:
            status = self.env["ihub.state"].search([["name", "=", "Created"]])
        return status

    @api.model
    def compute_children(self):
        """Computes the list of children of the super integration.

        :returns: List of instantiable integrations
        """
        return [(child, child) for child in self._inherits_children]

    @api.model
    def compute_status_name(self):
        """Computes the status_name field."""
        for res in self:
            res.status_name = res.status.name

    def compute_sub_id(self):
        """Finds sub_id.

        Iterates over models inheriting from this class and finds one whose super_id is equal to self.id.
        """
        if not self.sub_id:
            for child in self._inherits_children:
                if child != "ihub.abstract_integration":
                    sub_instance = self.env[child].search([["super_id", "=", self.id]])
                    if sub_instance:
                        self.sub_id = f"{child},{sub_instance.id}"
                        return

    @api.onchange("job_next_run")
    @api.depends("job_next_run")
    def check_next_run_date(self):
        """Checks that the next run is set to be in the future."""
        if self.job_next_run < datetime.now():
            raise exceptions.UserError("Next job time must be set in the future.")
        if not self.job_last_run:
            self.job_last_run = self.job_next_run - timedelta(days=1)

    def start(self):
        """Starts this integration"""
        sudo = self.sudo()

        sudo.set_status("Created")
        if not sudo.sub_is_job:
            # No need to set up jobs.
            sudo.set_status("Running")
            return

        if not sudo.job_next_run:
            raise exceptions.UserError("No next job date set.")

        if sudo.job_id:
            if sudo.job_id.state != "failed":
                sudo.unlink_if_exists(sudo.job_id)
        sudo.unlink_if_exists(sudo.cron_id)

        if sudo.job_next_run < fields.Datetime.now():
            interval = sudo._interval()
            date = sudo.job_next_run
            if interval:
                while date < fields.Datetime.now():
                    date += interval
                sudo.job_next_run = date
            else:
                sudo.job_next_run = date

        sudo.create_cron_job()
        sudo.create_next_job()
        sudo.set_status("Running")

    def stop(self):
        """Stops this integration.

        Deletes connected job and cron and sets status.
        """
        sudo = self.sudo()
        if sudo.status.name == "Running":
            sudo.unlink_if_exists(sudo.job_id)
            sudo.unlink_if_exists(sudo.cron_id)
            sudo.set_status("Stopped")

    def open_logs(self):
        """Returns the events view for this integration."""
        return {
            "name": "Events",
            "type": "ir.actions.act_window",
            "res_model": "ihub.event",
            "domain": [["integration_id", "=", self.id]],
            "view_mode": "tree,form",
        }

    @api.model
    def run_since_last_run(self):
        """Runs this integration starting from the last run."""
        self.run_from(self.job_last_run)

    @api.model
    def run_from(self, _from: datetime):
        """Runs this integration starting from the given datetime."""
        self.run_from_to(_from, datetime.now())

    @api.model
    def static_run_job(self, integration_id):
        """Entry point for the cron job. Runs the integration with the given id."""
        integration = self.env["ihub.integration"].browse(integration_id)
        integration.sudo().run_job()

    def run_job(self):
        """Runs this integration, setting job status and next run datetimes."""
        if self.status.name != "Running":
            return

        _from = self._get_last_run()
        _to = self.job_next_run

        # This leads to a concurrent update.
        # with self.while_running():
        #     self.run_manual_job(_from, _to)
        self.run_manual_job(_from, _to)

        # Jobs may set this status to failed in run_manual_job, we don't update the values in that case.
        if self.status.name == "Running":
            self.job_last_run = self.job_next_run
            self.job_id.done()
            self._increment_next_run()
            self.create_next_job()

    @contextmanager
    def while_running(self):
        """Context setting the current job state to running.

        BUGGY: Leads to concurrent update errors.
        """
        with new_environment(self) as env:
            self_c = env["ihub.integration"].browse(self.id)
            self_c.job_id.state = "running"
        yield

    def run_manual_job(self, _from: datetime, _to: datetime):
        """Doesn't set last run and increment next run time.

        If manual is set to true, on failure, the cron job is deleted. (this isn't possible inside the job).
        :param _from: from datetime
        :param _to: to datetime
        """
        # Overwrite scheduler user company
        self.env.company = self.company_id or self.env.company
        bot_user_id = self.env.ref("base.user_root")

        try:
            self.with_user(bot_user_id.id).with_context(
                allowed_company_ids=[self.company_id.id]
            ).run_from_to(_from, _to)

            # Only log successful run, if subintegration didn't call fail()
            if self.status.name == "Running" or self.is_manual():
                time_period_string = ""
                if self.sub_has_time_period:
                    time_period_string = f" for interval [{_from}+00:00, {_to}+00:00]"

                self.message_post(
                    body=f"Ran {'manually' if self.is_manual() else 'job'}{time_period_string}.",
                    message_type="comment",
                )
        except IHubInterruptException:
            # This has been called internally, meaning that the error has been logged and
            # we want to just skip all further processing.
            self.set_failed()
        except exceptions.UserError as e:
            if self.env.context.get("ihub_manual"):
                # On a manual run, we don't want to set an integration to failed and log UserExceptions
                raise e
            else:
                # this logs, sets failed state and raises exception
                self._handle_exception(e)
        except BaseException as e:
            # this logs, sets failed state and raises exception
            self._handle_exception(e)

    def create_next_job(self):
        """Creates a new job."""
        self.job_id = self.env["ihub.job"].create(
            dict(
                integration_id=self.id,
                function="run_job",
                from_date=self._get_last_run(),
                to_date=self.job_next_run,
                name=self.name,
            )
        )

    def _increment_next_run(self):
        """Sets job_next_run."""
        if self.job_interval_scalar and self.job_interval_unit:
            delta = self._interval()

            # increment job, handling rare cases where job gets out of sync with cron
            date = self.job_next_run + delta
            if self.cron_next_run:
                while date < self.cron_next_run - delta:
                    date += delta

            self.job_next_run = date

    def _interval(self):
        """Calculates the timedelta interval based on this integrations settings."""
        return timedelta(**{self.job_interval_unit: self.job_interval_scalar})

    def _get_last_run(self):
        """Gets last run, default of minus one day.

        :returns: datetime of last run
        """
        last_time = self.job_last_run
        if not self.job_last_run:
            last_time = self.job_next_run - timedelta(days=1)
        return last_time

    def _handle_exception(self, e):
        """Logs the exception, then propagates the exception again.

        :param e: Exception to log and propagate
        :raise BaseException: passed exception
        """
        self.ihub_error(
            summary=f"Unexpected Exception",
            details=traceback.format_exc(),
            related=None,
            integration=self.sub_id,
        )
        self.set_failed()
        raise e

    def set_failed(self):
        """Sets state to 'failed' using a new database cursor.

        This change gets committed, even if exceptions are raised.
        Rolls back all changes on main cursor.
        """
        with new_environment(self) as env:
            self_c = (
                env["ihub.integration"].browse(self.id).with_context(self.env.context)
            )
            self_c.set_status("Failed")

            # We can't modify the cron_id if the job is ran by that cron.
            # On the other hand, if the cron is running this job, it will deactivate itself on failure.
            if self.is_manual():
                self_c.unlink_if_exists(self_c.cron_id)

            self_c.send_chatter_error_message()
            self_c.job_id.fail()

        self.env.cr.rollback()

    def is_manual(self):
        """Whether the current run is a manual run."""
        return self.env.context.get("ihub_manual", False)

    def send_chatter_error_message(self):
        """Send error message in chatter.

        Send a note if manual, since there's no need to send notifications if the calling user is in the view.
        Send a notification/email if the job is ran automatically.
        """
        if self.is_manual():
            self.message_post(
                body=f"""
                        <b style="font-weight:bolder">
                            <font style="color:rgb(255, 0, 0)">
                                Failed manual run.
                            </font>
                        </b>
                        """,
                message_type="comment",
            )
        else:
            self.send_error_mail()

    def send_error_mail(self):
        """
        Send out email. Will also be written to chatter.
        """
        mail_template_id = self.env.ref("ihub.error_mail_template")
        mapped_email = {"recipient_ids": self.message_partner_ids}
        # noinspection PyBroadException
        try:
            self.env["mail.template"].browse(mail_template_id.ids).send_mail(
                self.id,
                email_values=mapped_email,
                force_send=True,
                raise_exception=True,
            )
        except BaseException as e:
            self.ihub_error(
                summary="Failed to send error notifications",
                details=f"error: {str(e)}",
                integration=self.sub_id,
            )

    def unlink(self):
        """Overwrites unlink to also delete the job and the cron."""
        self.unlink_if_exists(self.job_id)
        self.unlink_if_exists(self.cron_id)
        return super().unlink()

    def create_cron_job(self):
        """Creates a new cron job which runs static_run_job with the id of this object."""
        model_id = self.env["ir.model"].search([["model", "=", "ihub.integration"]])
        self.cron_id = self.env["ir.cron"].create(
            dict(
                name=f"IHub: {self.name}",
                model_id=model_id.id,
                interval_number=self.job_interval_scalar,
                interval_type=self.job_interval_unit,
                nextcall=self.job_next_run + self.sub_id.delay,
                active=True,
                numbercall=-1,
                state="code",
                code=f"model.static_run_job({self.id})",
            )
        )

    @staticmethod
    def unlink_if_exists(field):
        """Checks that a field exists before unlinking it."""
        if field.exists():
            field.unlink()
