"""
This module defines general decorators to define the Calm Application.
"""
from calm.resource import Resource
from calm.ex import DefinitionError, ClientError


def _set_handler_attribute(func, attr, value):
    """
    This checks whether the function is already defined as a Calm handler or
    not and sets the appropriate attribute based on that. This is done in
    order to not enforce a particular order for the decorators.
    """
    if getattr(func, 'handler_def', None):
        setattr(func.handler_def, attr, value)
    else:
        setattr(func, attr, value)


def produces(resource_type):
    """Decorator to specify what kind of Resource the handler produces."""
    if not issubclass(resource_type, Resource):
        raise DefinitionError('@produces value should be of type Resource.')

    def decor(func):
        """The function wrapper."""
        _set_handler_attribute(func, 'produces', resource_type)

        return func

    return decor


def consumes(resource_type):
    """Decorator to specify what kind of Resource the handler consumes."""
    if not issubclass(resource_type, Resource):
        raise DefinitionError('@consumes value should be of type Resource.')

    def decor(func):
        """The function wrapper."""
        _set_handler_attribute(func, 'consumes', resource_type)

        return func

    return decor


def fails(*errors):
    """Decorator to specify the list of errors returned by the handler."""
    for error in errors:
        if not issubclass(error, ClientError):
            raise DefinitionError('@fails accepts only subclasses of '
                                  'calm.ex.ClientError')

    def decor(func):
        """The function wrapper."""
        _set_handler_attribute(func, 'errors', errors)

        return func

    return decor
