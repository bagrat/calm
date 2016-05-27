# Calm

Calm is an extension to Tornado Framework that provides decorators and other
tools to easily implement RESTful APIs. The purpose of Calm is to ease the
process of defining your API, parsing argument values in the request handlers,
etc.

## Let's code!

Here is a basic usage example of Calm:

```
import tornado.ioloop
from calm import Application


app = Application()


@app.get('/hello/:your_name')
async def hello_world(request, your_name):
    return {'hello': your_name}


tornado_app = app.make_app()
tornado_app.listen(8888)
tornado.ioloop.IOLoop.current().start()
```

Now go ahead and try your new application! Navigate to
`http://localhost:8888/hello/YOUR_NAME_HERE` and see what you get.

## Contributions

Calm loves Pull Requests and welcomes any contribution be it an issue,
documentation or code. A good start for a contribution can be reviewing existing
open issues and trying to fix one of them.

If you find nothing to work on but cannot kill the urge, jump into the [gitter
channel](https://gitter.im/n9code/calm) and ask "what can I do?".
