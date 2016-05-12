import json
from datetime import datetime
import iso8601


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
