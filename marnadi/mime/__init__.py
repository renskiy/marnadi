class DataStreamer(type):

    def __call__(cls, stream, headers, content_params):
        decoder = super(DataStreamer, cls).__call__()
        return decoder(stream, headers, content_params)


class Decoder(object):

    __metaclass__ = DataStreamer

    def __call__(self, stream, headers, content_params):
        return ''.join(stream)