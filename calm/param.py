from inspect import Parameter as P

from calm.ex import DefinitionError


class Parameter(object):
    def __init__(self, name, param_type, param_in, default=P.empty):
        super().__init__()

        # TODO: add param description
        self.name = name
        self.param_type = param_type if param_type is not P.empty else str
        try:
            self.json_type = ParameterJsonType.from_python_type(self.param_type)
        except TypeError as ex:
            raise DefinitionError(
                "Wrong argument type for '{}'".format(name)
            ) from ex
        self.param_in = param_in
        self.required = default is P.empty
        self.default = default if default is not P.empty else None

    def generate_swagger(self):
        swagger = {
            'name': self.name,
            'in': self.param_in,
            'type': self.json_type,
            'required': self.required
        }

        if self.json_type == 'array':
            swagger['items'] = self.json_type.params['items']

        if not self.required:
            swagger['default'] = self.default

        return swagger


class PathParam(Parameter):
    def __init__(self, name, param_type):
        super().__init__(name, param_type, 'path')


class QueryParam(Parameter):
    def __init__(self, name, param_type, default=P.empty):
        super().__init__(name, param_type, 'query', default)


class ParameterJsonType(str):
    """An extended representation of a JSON type."""
    basic_type_map = {
        int: 'integer',
        float: 'number',
        str: 'string',
        bool: 'boolean'
    }

    def __init__(self, name):
        super().__init__()

        self.name = name
        self.params = {}

    @classmethod
    def from_python_type(cls, python_type):
        """Converts a Python type to a JsonType object."""
        if isinstance(python_type, list):
            if len(python_type) != 1:
                raise TypeError(
                    "Array type can contain only one element, i.e item type."
                )

            if isinstance(python_type[0], list):
                raise TypeError("Wrong parameter type: list of lists.")

            json_type = ParameterJsonType('array')
            json_type.params['items'] = cls.from_python_type(python_type[0])

            return json_type

        if isinstance(python_type, type):
            if python_type in cls.basic_type_map:
                # This is done to check direct equality to avoid subclass
                # anomalies, e.g. `bool` is a subclass of `int`.
                return ParameterJsonType(cls.basic_type_map[python_type])

            for supported_type in cls.basic_type_map:
                if issubclass(python_type, supported_type):
                    return ParameterJsonType(
                        cls.basic_type_map[supported_type]
                    )

        raise TypeError(
            "No associated JSON type for '{}'".format(python_type)
        )
