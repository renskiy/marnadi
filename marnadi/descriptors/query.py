import urlparse

from marnadi.descriptors import Descriptor


class Query(Descriptor):

    def clone(self, handler):
        return self.decode(handler.environ)

    @staticmethod
    def decode(environ):
        try:
            return urlparse.parse_qs(
                environ.query_string,
                keep_blank_values=True,
            )
        except AttributeError:  # query_string not in environ
            return {}