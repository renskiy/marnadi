import itertools
import collections

from marnadi.utils import Lazy, CachedDescriptor

from . import decoders


class Data(CachedDescriptor, collections.Mapping):

    __slots__ = '_content_decoders',

    def __init__(self, *content_decoders, **kw_content_decoders):
        super(Data, self).__init__()
        self._content_decoders = {
            content_type: Lazy(content_decoder)
            for content_type, content_decoder in itertools.chain(
                content_decoders,
                kw_content_decoders.items(),
            )
        }

    def __getitem__(self, content_type):
        return self._content_decoders[content_type]

    def __iter__(self):
        return iter(self._content_decoders)

    def __len__(self):
        return len(self._content_decoders)

    def get_value(self, request):
        decoder = self.get(request.content_type.value, decoders.Decoder)
        return decoder(request)
