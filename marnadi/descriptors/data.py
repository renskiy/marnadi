import importlib

from marnadi import mime
from marnadi.descriptors import Descriptor


class Data(Descriptor):

    def __init__(self, *content_decoders):
        super(Data, self).__init__()
        self.content_decoders = dict(content_decoders)

    def clone(self, owner_instance):
        return self.decode(
            owner_instance.environ['wsgi.input'],
            owner_instance.headers,
        )

    def decode(self, stream, headers):
        content_type, content_params = headers.get_splitted('Content-Type')
        decode = self.get_decoder(content_type)
        return decode(stream, headers, content_params)

    def get_decoder(self, content_type):
        if content_type not in self.content_decoders:
            return mime.Decoder  # default mime decoder
        decoder = self.content_decoders[content_type]
        if not callable(decoder):
            module_name, decoder_name = str(decoder).rsplit('.', 1)
            decoder_module = importlib.import_module(module_name)
            decoder = getattr(decoder_module, decoder_name)
            self.content_decoders[content_type] = decoder
        return decoder
