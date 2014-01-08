import importlib
json = importlib.import_module('json')  # import built-in module 'json'

from marnadi import mime


class Decoder(mime.Decoder):

    def __call__(self, stream, headers):
        encoding = headers.get_parsed('Content-Type')[1].get('charset', 'utf-8')
        return json.load(stream, encoding=encoding)