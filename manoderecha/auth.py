from requests.auth import HTTPBasicAuth


class ManoderechaAuth(HTTPBasicAuth):
    """
    Basic HTTP Authentication with custom header
    """
    def __call__(self, r):
        request = super(ManoderechaAuth, self).__call__(r)
        request.headers['Api-Authorization'] = request.headers['Authorization']
        return request
