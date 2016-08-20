from unittest import TestCase

from calm.param import ParameterJsonType


class CodecTests(TestCase):
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
