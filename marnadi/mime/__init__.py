class DataStreamer(type):

    def __call__(cls, stream, **content_params):
        decoder = super(DataStreamer, cls).__call__()
        return decoder(stream, **content_params)


class Decoder(object):

    __metaclass__ = DataStreamer

    def __call__(self, stream, **content_params):
        return ''.join(stream)