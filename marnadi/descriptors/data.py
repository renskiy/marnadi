from marnadi import mime, Lazy
from marnadi.descriptors import Descriptor


class Data(Descriptor):

    def __init__(self, *content_decoders):
        super(Data, self).__init__()
        self.content_decoders = dict(
            (
                content_type, (
                    content_decoder
                    if isinstance(content_decoder, Lazy) else
                    Lazy(content_decoder)
                )
            )
            for content_type, content_decoder in (
                content_decoders.iteritems()
                if isinstance(content_decoders, dict) else
                content_decoders
            )
        )

    def get_value(self, handler):
        stream = handler.environ['wsgi.input']
        content_type, content_params = \
            handler.headers.get_parsed('Content-Type')
        decoder = self.content_decoders.get(content_type, mime.Decoder)
        return decoder(stream, **content_params)
