

class CalmError(Exception):
    pass


class ClientError(CalmError):
    code = None
    message = None


class BadRequestError(ClientError):
    code = 400


class ArgumentParseError(BadRequestError):
    pass


class MethodNotAllowedError(ClientError):
    code = 405
    message = "Method not allowed"


class ServerError(CalmError):
    pass


class DefinitionError(ServerError):
    pass
