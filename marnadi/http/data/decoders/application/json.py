import functools
import importlib
json = importlib.import_module('json')  # import built-in module 'json'

from marnadi.errors import HttpError
from marnadi.http.data.decoders import Decoder as BaseDecoder


class Decoder(BaseDecoder):

    __slots__ = 'read',

    def __call__(self, request):
        self.read = functools.partial(
            self._read,
            stream=request.input,
            encoding=request.content_type.get('charset', 'utf-8'),
            size=request.content_length,
        )
        try:
            return json.load(self)
        except ValueError:
            raise HttpError('400 Bad Request')

    @staticmethod
    def _read(stream, encoding, size=0):
        return stream.read(size).decode(encoding=encoding)
