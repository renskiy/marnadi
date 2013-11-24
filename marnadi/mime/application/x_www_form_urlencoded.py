import urlparse

from marnadi import mime


class Decoder(mime.Decoder):

    def __call__(self, stream, **content_params):
        return urlparse.parse_qsl(
            ''.join(stream),
            keep_blank_values=True,
        )