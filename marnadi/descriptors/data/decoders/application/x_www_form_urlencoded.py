try:
    from urllib import parse
except ImportError:
    import urlparse as parse

from .. import Decoder as BaseDecoder


class Decoder(BaseDecoder):

    def __call__(self, stream, headers):
        return parse.parse_qs(
            ''.join(stream),
            keep_blank_values=True,
        )