class Empty(object):
    pass


class Descriptor(object):
    """Base class for managers.

    All custom managers should be inherited from this class.
    """

    def __init__(self, name=None):
        self.name = name
        self.environ = None

    def __get__(self, owner_instance, owner_class):
        assert self.name, "descriptor must have 'name' property"
        clone = self.clone(owner_instance)
        setattr(owner_instance, self.name, clone)
        return clone

    def clone(self, owner_instance):
        clone = Empty()
        clone.__class__ = self.__class__
        clone.environ = owner_instance.environ
        return clone