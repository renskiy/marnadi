from marnadi import mime, Lazy
from marnadi.descriptors import Descriptor


class Data(Descriptor):

    def __init__(self, *content_decoders):
        super(Data, self).__init__()
        self.content_decoders = dict(
            (content_type, Lazy(content_decoder))
            for content_type, content_decoder in (
                content_decoders.iteritems()
                if isinstance(content_decoders, dict) else
                content_decoders
            )
        )

    def get_value(self, handler):
        return self.decode(
            handler.environ['wsgi.input'],
            handler.headers,
        )

    def decode(self, stream, headers):
        content_type, content_params = headers.get_splitted('Content-Type')
        decode = self.get_decoder(content_type)
        return decode(stream, **content_params)

    def get_decoder(self, content_type):
        return self.content_decoders.get(content_type, mime.Decoder)
