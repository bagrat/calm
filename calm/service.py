class CalmService(object):
    def __init__(self, app, url):
        super(CalmService, self).__init__()

        self._app = app
        self._url = url

    def get(self, *url):
        return self._app.get(self._url, *url)

    def post(self, *url):
        return self._app.post(self._url, *url)

    def put(self, *url):
        return self._app.put(self._url, *url)

    def delete(self, *url):
        return self._app.delete(self._url, *url)
