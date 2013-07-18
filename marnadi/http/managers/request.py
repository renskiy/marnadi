from marnadi.http.managers import Manager, RequestHeaders


class RequestQuery(Manager):
    # TODO finish implementation

    pass


class RequestBody(Manager):
    # TODO finish implementation

    pass


class Request(Manager):

    query = RequestQuery()

    headers = RequestHeaders()

    body = RequestBody()