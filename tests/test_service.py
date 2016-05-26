from calm.testing import CalmTestCase
from calm import Application


app = Application()
service1 = app.service('/service1')
service2 = app.service('/service2')


@service1.get('/url1/:retparam')
def service1_url1(request, retparam):
    return retparam


@service1.put('/url2/:retparam')
def service1_url2(request, retparam):
    return retparam


@service2.post('/url1/:retparam')
def service2_url2(request, retparam):
    return retparam


@service2.delete('/url2/:retparam')
def service2_url3(request, retparam):
    return retparam


@app.delete('/applevel/:retparam')
def applevel(request, retparam):
    return retparam


class CalmServiceTests(CalmTestCase):
    def get_calm_app(self):
        global app
        return app

    def test_service(self):
        self.get('/service1/url1/something',
                 expected_code=200,
                 expected_result='something')

        self.put('/service1/url2/something',
                 expected_code=200,
                 expected_result='something')

        self.post('/service2/url1/something',
                  expected_code=200,
                  expected_result='something')

        self.delete('/service2/url2/something',
                    expected_code=200,
                    expected_result='something')

        self.delete('/applevel/something',
                    expected_code=200,
                    expected_result='something')
