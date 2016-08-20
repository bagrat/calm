from unittest import TestCase
from unittest.mock import MagicMock

from calm.codec import ArgumentParser
from calm.ex import DefinitionError


class CodecTests(TestCase):
    def test_argument_parser(self):
        parser = ArgumentParser()

        expected = 567
        actual = parser.parse(int, expected)

        self.assertEqual(expected, actual)
        self.assertRaises(DefinitionError, parser.parse, tuple, "nvm")

    def test_custom_type(self):
        custom_type = MagicMock()

        parser = ArgumentParser()

        parser.parse(custom_type, 1234)

        custom_type.parse.assert_called_once_with(1234)
