from marnadi.descriptors import Descriptor


class Data(Descriptor):

    def __init__(self, *content_decoders, **kwargs):
        super(Data, self).__init__(**kwargs)
        # TODO may contain strings or modules
        # TODO replace strings by modules once they have been loaded
        self._decoders = dict(content_decoders)

    def clone(self, owner_instance):
        instance = super(Data, self).clone(owner_instance)
        instance._decoders = self._decoders
        return instance

    @property
    def content_decoders(self):
        return tuple(self._decoders.items())