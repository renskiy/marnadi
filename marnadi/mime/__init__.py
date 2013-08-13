from marnadi import errors


class DataStreamer(type):

    BLOCK_SIZE = 8192

    def __call__(cls, stream, headers, content_params):
        try:
            content_length = int(headers['Content-Length'])
        except TypeError:
            raise errors.HttpError(errors.HTTP_400_BAD_REQUEST)
        except KeyError:
            raise errors.HttpError(errors.HTTP_411_LENGTH_REQUIRED)
        decoder = super(DataStreamer, cls).__call__()
        content_iterator = cls.iterator(stream, content_length)
        return decoder(content_iterator, headers, content_params)

    def iterator(cls, stream, content_length):
        bytes_left = content_length
        while bytes_left > 0:
            chunk_size = cls.get_chunk_size(bytes_left)
            yield stream.read(chunk_size)
            bytes_left -= chunk_size

    def get_chunk_size(cls, bytes_left):
        return (
            cls.BLOCK_SIZE
            if bytes_left > cls.BLOCK_SIZE else
            bytes_left
        )


class Decoder(object):

    __metaclass__ = DataStreamer

    def __call__(self, content, headers, content_params):
        return ''.join(content)