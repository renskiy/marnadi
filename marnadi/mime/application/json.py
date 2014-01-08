import importlib
json = importlib.import_module('json')  # import built-in module 'json'

from marnadi import mime


class Decoder(mime.Decoder):

    def __call__(self, stream, headers):
        return json.load(stream)