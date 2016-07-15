

def produces(resource_type):
    def decor(f):
        if getattr(f, 'handler_def', None):
            f.handler_def.produces = resource_type
        else:
            f.produces = resource_type

        return f

    return decor


def consumes(resource_type):
    def decor(f):
        if getattr(f, 'handler_def', None):
            f.handler_def.consumes = resource_type
        else:
            f.consumes = resource_type

        return f

    return decor
