class Empty(object):
    pass


class Descriptor(object):
    """Base class for managers.

    All custom managers should be inherited from this class.
    """

    def __init__(self):
        self.attr_name = None
        self.environ = None

    def __get__(self, owner_instance, owner_class):
        assert self.attr_name, "Descriptor need not empty `attr_name`"
        clone = self.clone(owner_instance)
        setattr(owner_instance, self.attr_name, clone)
        return clone

    @classmethod
    def clone(cls, owner_instance):
        clone = Empty()
        clone.__class__ = cls
        clone.environ = owner_instance.environ
        return clone