import urlparse

from marnadi.descriptors import Descriptor


class Query(Descriptor):

    def __init__(self, name=None):
        super(Query, self).__init__(name)
        self._query = None

    def clone(self, owner_instance):
        clone = super(Query, self).clone(owner_instance)
        clone._query = None
        return clone

    def __getitem__(self, query_param):
        value = self.get(query_param)
        if value is None:
            raise KeyError
        return value

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