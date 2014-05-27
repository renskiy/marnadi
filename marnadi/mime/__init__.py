from marnadi.utils import metaclass


class DecoderType(type):

    def __call__(cls, stream, headers):
        decoder = super(DecoderType, cls).__call__()
        return decoder(stream, headers)


@metaclass(DecoderType)
class Decoder(object):

    def __call__(self, stream, headers):
        return ''.join(stream)