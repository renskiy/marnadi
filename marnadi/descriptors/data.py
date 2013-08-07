from marnadi import mime
from marnadi.descriptors import Descriptor


class Data(Descriptor):

    def __init__(self, name=None, content_decoders=None, methods=None):
        super(Data, self).__init__(name)
        self.content_decoders = dict(content_decoders or ())
        self.headers = None
        self._body = None
        self.methods = methods or ()

    def clone(self, owner_instance):
        clone = super(Data, self).clone(owner_instance)
        assert clone.environ.request_method in self.methods, \
            'Data descriptor is not allowed for requested HTTP method, ' \
            'use `methods` keyword argument to set list of allowed methods'
        clone.content_decoders = self.content_decoders
        clone.headers = owner_instance.headers
        clone._body = None
        return clone

    def __str__(self):
        return str(self.body)

    def __len__(self):
        return len(self.body)

    def __iter__(self):
        return iter(self.body)

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
            return mime.Decoder
        # TODO load requested decoder
        # TODO replace string by callable once it has been loaded
