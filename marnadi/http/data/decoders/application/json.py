import functools
import importlib
json = importlib.import_module('json')  # import built-in module 'json'

from marnadi.errors import HttpError
from marnadi.http.data.decoders import Decoder as BaseDecoder


class Decoder(BaseDecoder):

    __slots__ = 'read',

    def __call__(self, request):
        encoding = request.content_type.params.get('charset', 'utf-8')
        stream = request.input
        size = request.content_length
        self.read = functools.partial(self._read, stream, encoding, size)
        try:
            return json.load(self)
        except ValueError:
            raise HttpError('400 Bad Request')

    @staticmethod
    def _read(stream, encoding, size=0):
        return stream.read(size).decode(encoding=encoding)
