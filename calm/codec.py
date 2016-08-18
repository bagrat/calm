"""
This module defines a parser for Calm and the users.

Classes:
    ArgumentParser  - defines a parser base class that enables the users to
                      provide custom parsers to convert request ArgumentParser
                      (path, query) to custom types
"""

from calm.ex import DefinitionError, ArgumentParseError


class ArgumentParser(object):
    """
    Extensible default parser for request arguments (path, query).

    When specifying request arguments (path, query) types via annotations,
    an instance of this class (or subclass) is used to parse the argument
    values. This class defines the default type parsers, but can be further
    extended by the user, to add more built-in or custom types.

    The default types supported are:
        `int` - parses base 10 number string into `int` object

    To extend this class in a subclass, the user must define a class/instances
    attribute named `parser` which should be of type `dict`, mapping types to
    parser functions. The parser function should accept one argument, which is
    the raw request argument value, and should return the parsed value.

    For convenience it is recommended to define the parser functions as
    instance methods, and the provide the `parsers` as a `@property`.

    Example:
        class MyArgumentParser(ArgumentParser):
            def parse_list(self, value):
                # your implementation here

                return parsed_value

            @property
            def parsers(self):
                return {
                    list: self.parse_list
                }

    If defined a custom argument parser by extending this class, the user must
    supply the subclass to the `calm.Application.configure` method, using the
    `argument_parser` key.

    Side Effects:
        `DefinitionError`    - raises when a parser is not implemented for a
                               requested type
        `ArgumentParseError` - raises when the parsing fails for some reason
    """
    def __init__(self):
        super(ArgumentParser, self).__init__()

        self._parsers = {
            int: self.parse_int
        }

    def parse(self, arg_type, value):
        """Parses the `value` to `arg_type` using the appropriate parser."""
        if arg_type not in self._parsers:
            if hasattr(arg_type, 'parse'):
                return arg_type.parse(value)

            raise DefinitionError(
                "Argument parser for '{}' is not defined".format(
                    arg_type
                )
            )

        return self._parsers[arg_type](value)

    @classmethod
    def parse_int(cls, value):
        """Parses a base 10 string to `int` object."""
        try:
            return int(value)
        except ValueError:
            raise ArgumentParseError(
                "Bad value for integer: {}".format(value)
            )


class ParameterJsonType(str):
    """An extended representation of a JSON type."""
    basic_type_map = {
        int: 'integer',
        float: 'number',
        str: 'string',
        bool: 'boolean'
    }

    def __init__(self, name):
        super().__init__()

        self.name = name
        self.params = {}

    @classmethod
    def from_python_type(cls, python_type):
        """Converts a Python type to a JsonType object."""
        if isinstance(python_type, list):
            if len(python_type) != 1:
                raise TypeError(
                    "Array type can contain only one element, i.e item type."
                )

            if isinstance(python_type[0], list):
                raise TypeError("Wrong parameter type: list of lists.")

            json_type = ParameterJsonType('array')
            json_type.params['items'] = cls.from_python_type(python_type[0])

            return json_type

        if isinstance(python_type, type):
            if python_type in cls.basic_type_map:
                # This is done to check direct equality to avoid subclass
                # anomalies, e.g. `bool` is a subclass of `int`.
                return ParameterJsonType(cls.basic_type_map[python_type])

            for supported_type in cls.basic_type_map:
                if issubclass(python_type, supported_type):
                    return ParameterJsonType(
                        cls.basic_type_map[supported_type]
                    )

        raise TypeError(
            "No associated JSON type for '{}'".format(python_type)
        )
