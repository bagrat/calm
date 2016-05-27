"""
This module defines encoders, decoders and parsers for Calm and the users.

Classes:
    CalmJSONEncoder - defines a custom json encoder to be used with json module
    CalmJSONDecoder - defines a custom json decoder to be used with json module
    ArgumentParser  - defines a parser base class that enables the users to
                      provide custom parsers to convert request ArgumentParser
                      (path, query) to custom types
"""

import json
from datetime import datetime
import iso8601

from calm.ex import DefinitionError, ArgumentParseError


class CalmJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that supports `datetime` serialization."""

    def default(self, obj):
        """
        Extends `json.JSONEncoder.default` to support `datetime` serialization.

        For `datetime` objects this method return the date encoded in ISO-8601
        standard. For all other objects, uses the default encoder.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()

        return super(CalmJSONEncoder, self).default(obj)  # pragma: no cover


class CalmJSONDecoder(json.JSONDecoder):
    """Custom JSON decoder that supports `datetime` deserialization."""

    def decode(self, s, *args, **kwargs):
        """
        Extends `json.JSONDecoder.decode` to decode ISO-8601 strings.

        This method deserializes a string into json, by converting all ISO-8601
        strings to `datetime` objects.
        """
        parsed = super(CalmJSONDecoder, self).decode(s, *args, **kwargs)
        return self._parse_date(parsed)

    def _parse_date(self, obj):
        """
        Converts ISO-8601 string occurrences to `datetime` objects.

        This method scans for ISO-8601 strings and parses them into `datetime`
        objects. The strings can be nested into other data structures like
        dicts and lists.
        """
        if isinstance(obj, str):
            try:
                return iso8601.parse_date(obj)
            except (iso8601.ParseError, TypeError):
                return obj
        elif isinstance(obj, list):
            return [self._parse_date(s) for s in obj]
        elif isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self._parse_date(value)

            return obj
        else:
            return obj


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
    parsers = {}

    def __init__(self):
        super(ArgumentParser, self).__init__()

        self._parsers = {**self._base_parsers, **self.parsers}  # noqa

    @property
    def _base_parsers(self):
        """Defines the default argument parsers."""
        return {
            int: self.parse_int
        }

    def parse(self, arg_type, value):
        """Parses the `value` to `arg_type` using the appropriate parser."""
        if arg_type not in self._parsers:
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
