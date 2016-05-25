import json
from datetime import datetime
import iso8601

from calm.ex import DefinitionError


class CalmJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()

        return super(CalmJSONEncoder, self).default(obj)  # pragma: no cover


class CalmJSONDecoder(json.JSONDecoder):
    def decode(self, obj):
        try:
            parsed = super(CalmJSONDecoder, self).decode(obj)
        except (json.decoder.JSONDecodeError, TypeError):
            parsed = obj

        if isinstance(parsed, str):
            try:
                return iso8601.parse_date(obj)
            except (iso8601.ParseError, TypeError):
                return parsed
        elif isinstance(parsed, list):
            return [self.decode(s) for s in parsed]
        elif isinstance(parsed, dict):
            for k, v in parsed.items():
                parsed[k] = self.decode(v)

            return parsed
        else:
            return parsed


class ArgumentParser(object):
    BASE_PARSERS = {
        int: int
    }
    parsers = {}

    def __init__(self):
        super(ArgumentParser, self).__init__()

        self._parsers = {**self.BASE_PARSERS, **self.parsers}

    def parse(self, arg_type, value):
        if arg_type not in self._parsers:
            raise DefinitionError(
                "Argument parser for '{}' is not defined".format(
                    arg_type
                )
            )

        return self._parsers[arg_type](value)
