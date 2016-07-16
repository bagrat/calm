from unittest import TestCase

from calm.codec import ArgumentParser
from calm.ex import DefinitionError


class CodecTests(TestCase):
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
