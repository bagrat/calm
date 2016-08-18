"""
This module defines general decorators to define the Calm Application.
"""
from calm.resource import Resource
from calm.ex import DefinitionError


def produces(resource_type):
    """Decorator to specify what kind of Resource the handler produces."""
    if not isinstance(resource_type, Resource):
        raise DefinitionError('@produces value should be of type Resource.')

    def decor(func):
        """
        The function wrapper.

        It checks whether the function is already defined as a Calm handler or
        not and sets the appropriate attribute based on that. This is done in
        order to not enforce a particular order for the decorators.
        """
        if getattr(func, 'handler_def', None):
            func.handler_def.produces = resource_type
        else:
            func.produces = resource_type

        return func

    return decor


def consumes(resource_type):
    """Decorator to specify what kind of Resource the handler consumes."""
    if not isinstance(resource_type, Resource):
        raise DefinitionError('@consumes value should be of type Resource.')

    def decor(func):
        """
        The function wrapper.

        It checks whether the function is already defined as a Calm handler or
        not and sets the appropriate attribute based on that. This is done in
        order to not enforce a particular order for the decorators.
        """
        if getattr(func, 'handler_def', None):
            func.handler_def.consumes = resource_type
        else:
            func.consumes = resource_type

        return func

    return decor
