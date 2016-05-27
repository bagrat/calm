"""
It is always Calm before a Tornado!

Calm is a Tornado extension providing tools and decorators to easily develop
RESTful APIs based on Tornado.

The core of Calm is the Calm Application. The users should initialize an
(or more) instance of `calm.Application` and all the rest is done using that
instance.

The whole idea of Calm is to follow the common pattern of frameworks, where the
user defines handlers and decorates them with appropriate HTTP methods and
assigns URIs to them. Here is a basic example:

    from calm import Application

    app = Application()


    @app.get('/hello/:your_name')
    def hello_world(request, your_name):
        return "Hello %s".format(your_name)

For more information see `README.md`.
"""
from calm.core import CalmApp as Application

__all__ = ['Application']
__version__ = '0.1.4'
