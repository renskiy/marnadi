class DecoderType(type):

    def __call__(cls, stream, headers):
        decoder = super(DecoderType, cls).__call__()
        return decoder(stream, headers)


class Decoder(object):

    __metaclass__ = DecoderType

    def __call__(self, stream, headers):
        return ''.join(stream)