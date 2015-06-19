from marnadi.utils import metaclass


class DecoderType(type):

    def __call__(cls, request):
        decoder = super(DecoderType, cls).__call__()
        return decoder(request)


@metaclass(DecoderType)
class Decoder(object):

    __slots__ = ()

    def __call__(self, request):
        content_type = request.content_type
        encoding = content_type and content_type.params.get(
            'charset') or 'utf-8'
        return request.input.read(request.content_length).decode(
            encoding=encoding)
