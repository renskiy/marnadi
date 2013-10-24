import urlparse

from marnadi import mime


class Decoder(mime.Decoder):

    def __call__(self, stream, headers, content_params):
        return urlparse.parse_qs(
            ''.join(stream),
            keep_blank_values=True,
        )