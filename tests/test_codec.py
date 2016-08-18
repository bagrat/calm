from unittest import TestCase
from unittest.mock import MagicMock

from calm.codec import ArgumentParser, ParameterJsonType
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

    def test_param_json_type(self):
        pjt = ParameterJsonType.from_python_type(int)
        self.assertEqual(pjt, 'integer')

        pjt = ParameterJsonType.from_python_type(float)
        self.assertEqual(pjt, 'number')

        pjt = ParameterJsonType.from_python_type(str)
        self.assertEqual(pjt, 'string')

        pjt = ParameterJsonType.from_python_type(bool)
        self.assertEqual(pjt, 'boolean')

        pjt = ParameterJsonType.from_python_type([bool])
        self.assertEqual(pjt, 'array')
        self.assertEqual(pjt.params['items'], 'boolean')

        class CustomType(str):
            pass

        pjt = ParameterJsonType.from_python_type(CustomType)
        self.assertEqual(pjt, 'string')

    def test_param_json_type_errors(self):
        self.assertRaises(TypeError,
                          ParameterJsonType.from_python_type,
                          [int, str])

        self.assertRaises(TypeError,
                          ParameterJsonType.from_python_type,
                          [[int]])

        self.assertRaises(TypeError,
                          ParameterJsonType.from_python_type,
                          tuple)
