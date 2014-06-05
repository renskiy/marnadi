import itertools

from marnadi import mime
from marnadi.descriptors import Descriptor
from marnadi.utils import Lazy


class Data(Descriptor):

    def __init__(self, *content_decoders, **kw_content_decoders):
        super(Data, self).__init__()
        self.content_decoders = {
            content_type: Lazy(content_decoder)
            for content_type, content_decoder in itertools.chain(
                content_decoders,
                kw_content_decoders.items(),
            )
        }

    def get_value(self, handler):
        stream = handler.environ['wsgi.input']
        content_type = handler.environ.get('CONTENT_TYPE', '').split(';', 1)[0]
        decoder = self.content_decoders.get(content_type, mime.Decoder)
        return decoder(stream, handler.headers)
