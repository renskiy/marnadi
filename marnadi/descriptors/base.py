class Empty(object):
    pass


class Descriptor(object):
    """Base class for managers.

    All custom managers should be inherited from this class.
    """

    def __init__(self):
        self.attr_name = None
        self.environ = None

    def __get__(self, handler, handler_class):
        assert self.attr_name, "Descriptor need not empty `attr_name`"
        clone = self.clone(handler)
        setattr(handler, self.attr_name, clone)
        return clone

    @classmethod
    def clone(cls, handler):
        clone = Empty()
        clone.__class__ = cls
        clone.environ = handler.environ
        return clone