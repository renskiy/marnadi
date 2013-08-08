from marnadi import errors


class DataPreparer(type):

    def __call__(cls, stream, headers, content_params):
        try:
            content_length = int(headers['Content-Length'])
        except TypeError:
            raise errors.HttpError(errors.HTTP_400_BAD_REQUEST)
        except KeyError:
            raise errors.HttpError(errors.HTTP_411_LENGTH_REQUIRED)
        decoder = super(DataPreparer, cls).__call__()
        content = stream.read(content_length)
        return decoder(content, headers, content_params)


class Decoder(object):

    __metaclass__ = DataPreparer

    def __call__(self, content, headers, content_params):
        return content