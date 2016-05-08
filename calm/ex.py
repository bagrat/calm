

class CoreError(Exception):
    pass


class ClientError(Exception):
    code = None


class BadRequestError(ClientError):
    code = 400


class MethodNotAllowedError(ClientError):
    code = 405
    message = "Method not allowed"


class ServerError(Exception):
    pass
