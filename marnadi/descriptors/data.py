import importlib

from marnadi import mime
from marnadi.descriptors import Descriptor


class Data(Descriptor):

    def __init__(self, name=None, content_decoders=None, allowed_methods=None):
        super(Data, self).__init__(name)
        self.content_decoders = dict(content_decoders or ())
        self.headers = None
        self._body = None
        self.allowed_methods = allowed_methods or ()

    def clone(self, owner_instance):
        clone = super(Data, self).clone(owner_instance)
        assert clone.environ.request_method in self.allowed_methods, \
            'Data descriptor is not allowed for requested HTTP method, ' \
            'use `methods` keyword argument to set list of allowed methods'
        clone.content_decoders = self.content_decoders
        clone.headers = owner_instance.headers
        clone._body = None
        return clone

    def __contains__(self, name):
        return name in self.body

    def __getitem__(self, key):
        return self.body[key]

    @property
    def body(self):
        if self._body is None:
            self._body = self.decode()
        return self._body

    def get(self, name, default=None):
        if isinstance(self.body, dict):
            return self.body.get(name, default)
        return default

    def decode(self):
        content_type, content_params = self.headers.get_splitted('Content-Type')
        decode = self.get_decoder(content_type)
        return decode(self.environ['wsgi.input'], self.headers, content_params)

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
