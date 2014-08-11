import importlib
json = importlib.import_module('json')  # import built-in module 'json'

from marnadi.descriptors.data.decoders import Decoder as BaseDecoder


class Decoder(BaseDecoder):

    __slots__ = ('stream', 'encoding')

    def __init__(self):
        self.encoding = None
        self.stream = None

    def __call__(self, request):
        self.encoding = request.content_type.params.get('charset', 'utf-8')
        self.stream = request.input
        return json.load(self)

    def read(self, *args, **kwargs):
        assert self.encoding and self.stream, \
            "Either stream or encoding is not provided"
        return self.stream.read(*args, **kwargs).decode(encoding=self.encoding)
