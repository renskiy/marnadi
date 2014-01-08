class DataStreamer(type):

    def __call__(cls, stream, headers):
        decoder = super(DataStreamer, cls).__call__()
        return decoder(stream, headers)


class Decoder(object):

    __metaclass__ = DataStreamer

    def __call__(self, stream, headers):
        return ''.join(stream)