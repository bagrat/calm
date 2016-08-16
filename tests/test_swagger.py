from unittest.mock import patch

from calm.testing import CalmHTTPTestCase
from calm import Application


app = Application(name='testapp', version='1')


class Swaggertests(CalmHTTPTestCase):
    def get_calm_app(self):
        global app
        self.maxDiff = None
        return app

    def test_basic_info(self):
        test_app = Application(name='testapp', version='1', host='http://a.b',
                               base_path='/test', description='swagger test',
                               tos='terms of service')
        test_app.set_contact('tester', 'http://testurl.com', 'test@email.com')
        test_app.set_licence('name', 'http://license.url')

        expected_swagger = {
            'swagger': '2.0',
            'info': {
                'title': 'testapp',
                'version': '1',
                'description': 'swagger test',
                'termsOfService': 'terms of service',
                'contact': {
                    'name': 'tester',
                    'url': 'http://testurl.com',
                    'email': 'test@email.com'
                },
                'license': {
                    'name': 'name',
                    'url': 'http://license.url'
                }
            },
            'host': 'http://a.b',
            'basePath': '/test',
            'consumes': ['application/json'],
            'produces': ['application/json'],
        }

        actual_swagger = test_app.generate_swagger_json()
        actual_swagger.pop('responses')
        self.assertEqual(expected_swagger, actual_swagger)

    def test_error_responses(self):
        class SomeError():
            """some description"""

        someapp = Application(name='testapp', version='1')
        someapp.configure(error_key='wompwomp')

        self.assertEqual(someapp._generate_error_schema(), {
            'Error': {
                'properties': {
                    'wompwomp': {'type': 'string'}
                },
                'required': ['wompwomp']
            }
        })

        with patch('calm.ex.ClientError.get_defined_errors') as gde:
            gde.return_value = [SomeError]
            responses = someapp.generate_swagger_json().pop('responses')

            self.assertEqual(responses, {
                'SomeError': {
                    'description': 'some description',
                    'schema': {
                        '$ref': '#/definitions/Error'
                    }
                }
            })

    def test_swagger_json(self):
        with patch('calm.ex.ClientError.get_defined_errors') as gde:
            gde.return_value = []
            self.get('/swagger.json', expected_json_body={
                'swagger': '2.0',
                'info': {
                    'title': 'testapp',
                    'version': '1'
                },
                'produces': ['application/json'],
                'consumes': ['application/json']
            })
