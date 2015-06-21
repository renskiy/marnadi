import importlib
json = importlib.import_module('json')  # import built-in module 'json'

from marnadi.http import Error
from marnadi.http.data.decoders import Decoder as BaseDecoder


class Decoder(BaseDecoder):

    __slots__ = ()

    def __call__(self, request):
        try:
            return json.loads(super(Decoder, self).__call__(request))
        except ValueError:
            raise Error('400 Bad Request')
