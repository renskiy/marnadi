HTTP_200_OK = '200 OK'

HTTP_404_NOT_FOUND = '404 Not Found'
HTTP_405_METHOD_NOT_ALLOWED = '405 Method Not Allowed'

HTTP_500_INTERNAL_SERVER_ERROR = '500 Internal Server Error'


class HttpError(Exception):
    # TODO finish implementation

    status = HTTP_500_INTERNAL_SERVER_ERROR

    headers = ()

    def get_response(self):
        return ['HttpError']