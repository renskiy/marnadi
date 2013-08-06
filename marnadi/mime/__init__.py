from marnadi import errors


class DataPreparer(type):

    def __call__(cls, stream, headers, content_params):
        try:
            content_length = int(headers['Content-Length'])
        except TypeError:
            raise errors.HttpError(errors.HTTP_400_BAD_REQUEST)
        except KeyError:
            raise errors.HttpError(errors.HTTP_411_LENGTH_REQUIRED)
        if content_length == 0:
            return ''
        decoder = super(DataPreparer, cls).__call__()
        data = stream.read(content_length)
        return decoder(data, headers, content_params)


class Decoder(object):

    __metaclass__ = DataPreparer

    def __call__(self, data, headers, content_params):
        return data