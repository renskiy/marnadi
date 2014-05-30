from marnadi.utils import Empty


class Descriptor(object):
    """Base class for descriptors.

    All descriptors should inherit this class.
    """

    def __init__(self):
        self.name = None
        self.environ = None

    def __get__(self, handler, handler_class):
        if handler is None:
            return self  # static access
        assert self.name is not None
        value = handler.__dict__[self.name] = self.get_value(handler)
        return value

    def get_value(self, handler):
        return self.clone(environ=handler.environ)

    def clone(self, *copy_properties, **set_properties):
        clone = Empty()
        clone.__class__ = self.__class__
        clone.name = self.name
        for prop_name in copy_properties:
            try:
                clone.__dict__[prop_name] = self.__dict__[prop_name]
            except KeyError:
                pass
        clone.__dict__.update(set_properties)
        return clone
