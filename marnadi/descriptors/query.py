try:
    from urllib import parse
except ImportError:
    import urlparse as parse

from marnadi.descriptors import Descriptor


class Query(Descriptor):

    def get_value(self, handler):
        try:
            return parse.parse_qsl(
                handler.environ.query_string,
                keep_blank_values=True,
            )
        except AttributeError:  # query_string not in environ
            return ()
