"""Tools for supporting delegation inheritance.

In delegation inheritance, an object is created for both the super and the sub class.
The sub class has a reference to the super class (super_id) and in our case we also have a computed field
(sub_id) in the super class, referencing the sub class.
"""
from functools import wraps
import logging

LOGGER = logging.getLogger(__name__)


def sub(func):
    """Decorates a method of the super class in delegated inheritance, calls the same function of sub_id instead.

    If sub_id.func isn't implemented, call super_id.func instead.
    Basically delegates functions to a more specific instance.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.sub_id:
            self.compute_sub_id()

        sub_function = getattr(self.sub_id, func.__name__, None)
        if sub_function:
            return sub_function(*args, **kwargs)
        LOGGER.error(
            f"Sub function for {func.__name__} not found. Calling super function instead."
        )
        return func(self, *args, **kwargs)

    return wrapper
