import urlparse

from marnadi import mime


class Decoder(mime.Decoder):

    def __call__(self, content, headers, content_params):
        return urlparse.parse_qs(''.join(content), keep_blank_values=True)