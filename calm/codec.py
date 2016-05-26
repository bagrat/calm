import json
from datetime import datetime
import iso8601

from calm.ex import DefinitionError, ArgumentParseError


class CalmJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()

        return super(CalmJSONEncoder, self).default(obj)  # pragma: no cover


class CalmJSONDecoder(json.JSONDecoder):
    def decode(self, s):
        parsed = super(CalmJSONDecoder, self).decode(s)
        return self._parse_date(parsed)

    def _parse_date(self, obj):
        if isinstance(obj, str):
            try:
                return iso8601.parse_date(obj)
            except (iso8601.ParseError, TypeError):
                return obj
        elif isinstance(obj, list):
            return [self._parse_date(s) for s in obj]
        elif isinstance(obj, dict):
            for k, v in obj.items():
                obj[k] = self._parse_date(v)

            return obj
        else:
            return obj


class ArgumentParser(object):
    parsers = {}

    def __init__(self):
        super(ArgumentParser, self).__init__()

        self._parsers = {**self._base_parsers, **self.parsers}

    @property
    def _base_parsers(self):
        return {
            int: self.parse_int
        }

    def parse(self, arg_type, value):
        if arg_type not in self._parsers:
            raise DefinitionError(
                "Argument parser for '{}' is not defined".format(
                    arg_type
                )
            )

        return self._parsers[arg_type](value)

    def parse_int(self, value):
        try:
            return int(value)
        except ValueError:
            raise ArgumentParseError(
                "Bad value for integer: {}".format(value)
            )
