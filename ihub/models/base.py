import logging
from functools import lru_cache

from odoo import exceptions
from odoo import models

from ..lib.cursor import new_environment
from ..lib.exceptions import IHubInterruptException

LOGGER = logging.getLogger(__name__)


class Base(models.AbstractModel):
    """Extends base, to to listen to ihub events."""

    _inherit = "base"

    def ihub_create_and_log(self, level, summary, details, related, integration):
        """
        Creates a new event of the specified level.
        If the level is error, it will be written using an own cursor, so it appears even if an error occurs.
        """
        # If called from within integration, does not require integration=self.
        if not integration:
            if hasattr(self, "super_id") and self.super_id._name == "ihub.integration":
                integration = self

        integration = self._get_parent_integration(integration)

        if related:
            related = f"{related._name},{related.id}"
        # Use a new cursor to immediately commit warnings and errors
        commit = level in ["error"]
        if commit:
            with new_environment(self) as env:
                self._ihub_create_and_log(
                    env, level, summary, details, related, integration
                )
        else:
            self._ihub_create_and_log(
                self.env, level, summary, details, related, integration
            )
        return integration

    @staticmethod
    def _ihub_create_and_log(env, level, summary, details, related, integration):
        env["ihub.event"].create(
            dict(
                level=level,
                summary=summary,
                details=details,
                related=related,
                integration_id=integration.id if integration else None,
            )
        )
        getattr(LOGGER, level)(
            f"[{integration.name if integration else '?'}] {summary}: {details} "
            + (f"| Related to {related}" if related else "")
        )

    def ihub_info(
        self, summary: str = None, details: str = None, related=None, integration=None,
    ):
        """Info: e.g. an object was created successfully."""
        self.ihub_create_and_log("info", summary, details, related, integration)

    def ihub_warning(
        self,
        summary: str = None,
        details: str = None,
        error: str = None,  # for backwards compatibility
        related=None,
        integration=None,
    ):
        """Warnings: e.g. an object was created, but it is missing a few fields."""
        self.ihub_create_and_log("warning", summary, details, related, integration)

    def ihub_error(
        self,
        summary: str = None,
        details: str = None,
        error: str = None,  # for backwards compatibility
        related=None,
        integration=None,
        raised=False,
    ):
        """Errors: an object could not be created. These events are always written to database, even on rollback.

        If raised is set, a user error is returned instead if in a manual run.
        """
        if raised and self.env.context.get("ihub_manual"):
            return exceptions.UserError(f"{summary}. {details if details else ''}")
        else:
            integration = self.ihub_create_and_log(
                "error", summary, details, related, integration
            )
            if raised:
                return IHubInterruptException()

    @staticmethod
    def _get_parent_integration(integration):
        """Gets the ihub.integration for this integration.
        Supports multiple levels of inheritance."""
        while hasattr(integration, "super_id"):
            integration = integration.super_id
        return integration
