from unittest import TestCase
from datetime import datetime
import json
from calm.codec import CalmJSONEncoder, CalmJSONDecoder
import pytz


class CodecTests(TestCase):
    def test_codecs(self):
        expected = {
            'date': datetime(2001, 2, 3, 4, 5, 6, 7, tzinfo=pytz.utc),
            'list': [
                'hello',
                datetime(2003, 4, 5, 6, 7, 8, 9, tzinfo=pytz.utc),
                'world'
            ],
            'dict': {
                'subdoc': 5,
                'subdate': datetime(2002, 3, 4, 5, 6, 7, 8, tzinfo=pytz.utc)
            },
            'something': 'else'
        }

        encoded = json.dumps(expected, cls=CalmJSONEncoder)
        actual = json.loads(encoded, cls=CalmJSONDecoder)

        self.assertEqual(expected, actual)
