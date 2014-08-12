from marnadi.utils import metaclass


class DecoderType(type):

    def __call__(cls, request):
        decoder = super(DecoderType, cls).__call__()
        return decoder(request)


@metaclass(DecoderType)
class Decoder(object):

    __slots__ = ()

    def __call__(self, request):
        return b''.join(request.input)
