

def produces(resource_type):
    def decor(func):
        if getattr(func, 'handler_def', None):
            func.handler_def.produces = resource_type
        else:
            func.produces = resource_type

        return func

    return decor


def consumes(resource_type):
    def decor(func):
        if getattr(func, 'handler_def', None):
            func.handler_def.consumes = resource_type
        else:
            func.consumes = resource_type

        return func

    return decor
