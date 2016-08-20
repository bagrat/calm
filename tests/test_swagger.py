from unittest.mock import patch

from calm import Application
from calm.testing import CalmHTTPTestCase
from calm.decorator import produces, consumes, fails, deprecated
from calm.resource import Resource, Integer
from calm.ex import ClientError


app = Application(name='testapp', version='1')


class SomeProdResource(Resource):
    someint = Integer()


class SomeConsResource(Resource):
    someint = Integer()


class SomeError(ClientError):
    """some error"""
    code = 456


@app.post('/somepost/{somepatharg}')
@produces(SomeProdResource)
@consumes(SomeConsResource)
@fails(SomeError)
@deprecated
def somepost(self, somepatharg,
             somequeryarg: int,
             somelistarg: [bool],
             somedefaultarg: str = "default"):
    """
    Some summary.

    Some description.
    """
    pass


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
        actual_swagger.pop('definitions')
        actual_swagger.pop('paths')
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
        self.get('/swagger.json', expected_json_body={
            'swagger': '2.0',
            'info': {
                'title': 'testapp',
                'version': '1'
            },
            'produces': ['application/json'],
            'consumes': ['application/json'],
            'paths': {
                '/somepost/{somepatharg}': {
                    'post': somepost.handler_def.operation_definition
                }
            },
            'definitions': app._generate_swagger_definitions(),
            'responses': app._generate_swagger_responses()
        })

    def test_operation_definition(self):
        handler_def = somepost.handler_def

        expected_opdef = {
            'summary': 'Some summary.',
            'description': 'Some description.',
            'operationId': 'tests_test_swagger_somepost',
            'deprecated': True,
            'responses': {
                '200': {
                    'description': '',
                    'schema': {
                        '$ref': '#/definitions/SomeProdResource'
                    }
                },
                '456': {
                    '$ref': '#/responses/SomeError'
                }
            },
        }
        expected_parameters = [
                {
                    'name': 'somepatharg',
                    'in': 'path',
                    'required': True,
                    'type': 'string'
                },
                {
                    'name': 'somequeryarg',
                    'in': 'query',
                    'type': 'integer',
                    'required': True
                },
                {
                    'name': 'somedefaultarg',
                    'in': 'query',
                    'type': 'string',
                    'required': False,
                    'default': 'default'
                },
                {
                    'name': 'somelistarg',
                    'in': 'query',
                    'required': True,
                    'type': 'array',
                    'items': 'boolean'
                },
                {
                    'in': 'body',
                    'name': 'body',
                    'schema':  {
                        '$ref': '#/definitions/SomeConsResource'
                    }
                }
            ]
        actual_opdef = handler_def.operation_definition
        actual_parameters = actual_opdef.pop('parameters')

        self.assertEqual(expected_opdef, actual_opdef)
        self.assertCountEqual(expected_parameters, actual_parameters)
