import urlparse

from marnadi.descriptors import Descriptor


class Query(Descriptor):

    def __init__(self):
        super(Query, self).__init__()
        self._query = None

    def clone(self, handler):
        clone = super(Query, self).clone(handler)
        clone._query = None
        return clone

    def __contains__(self, name):
        return name in self.query

    def __getitem__(self, key):
        return self.query[key]

    @property
    def query(self):
        if self._query is None:
            try:
                self._query = urlparse.parse_qs(self.environ.query_string,
                                                keep_blank_values=True)
            except AttributeError:
                self._query = {}
        return self._query

    def get(self, query_param, default=None):
        return self.query.get(query_param, default)