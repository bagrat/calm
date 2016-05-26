from unittest import TestCase
from datetime import datetime
import json
import pytz

from calm.codec import CalmJSONEncoder, CalmJSONDecoder, ArgumentParser
from calm.ex import DefinitionError


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

    def test_codec_wrong(self):
        self.assertRaises(json.JSONDecodeError, json.loads, "not json",
                          cls=CalmJSONDecoder)

    def test_argument_parser(self):
        class MyArgParser(ArgumentParser):
            @property
            def parsers(self):
                return {
                    int: self.my_int_parser
                }

            def my_int_parser(self, value):
                return value + 1

        parser = MyArgParser()

        expected = 567
        actual = parser.parse(int, expected - 1)

        self.assertEqual(expected, actual)
        self.assertRaises(DefinitionError, parser.parse, str, "nvm")
