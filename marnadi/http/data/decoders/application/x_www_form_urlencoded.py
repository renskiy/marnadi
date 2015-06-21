try:
    from urllib import parse
except ImportError:
    import urlparse as parse

from marnadi.http.data.decoders import Decoder as BaseDecoder


class Decoder(BaseDecoder):

    __slots__ = ()

    def __call__(self, request):
        return dict(parse.parse_qsl(
            super(Decoder, self).__call__(request),
            keep_blank_values=True,
        ))
