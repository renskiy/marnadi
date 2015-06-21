from marnadi.http import Error
from marnadi.utils import metaclass


class DecoderType(type):

    def __call__(cls, request):
        decoder = super(DecoderType, cls).__call__()
        return decoder(request)


@metaclass(DecoderType)
class Decoder(object):

    __slots__ = ()

    default_encoding = 'utf-8'

    def __call__(self, request):
        return self.decode(
            data=request.input.read(request.content_length),
            encoding=self.get_encoding(request.content_type)
        )

    def get_encoding(self, content_type):
        return content_type and content_type.params.get(
            'charset') or self.default_encoding

    @staticmethod
    def decode(data, encoding):
        try:
            return data.decode(encoding=encoding)
        except UnicodeDecodeError:
            raise Error('400 Bad Request')
