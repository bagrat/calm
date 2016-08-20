from untt.util import parse_docstring


def generate_error_definition(error):
    summary, description = parse_docstring(error.__doc__)
    doc_split = [summary, '\n', 'description'] if description else [summary]
    return {
        'description': '\n'.join(doc_split),
        'schema': {
            '$ref': '#/definitions/Error'
        }
    }
