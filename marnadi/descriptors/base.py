class Descriptor(object):
    """Base class for descriptors.

    All descriptors should inherit this class.
    """

    def __init__(self):
        self.attr_name = None
        self.environ = None

    def __get__(self, handler, handler_class):
        if handler is None:
            return self  # static access
        if self.attr_name is None:
            raise ValueError("Descriptor's `attr_name` can't be None")
        value = handler.__dict__[self.attr_name] = self.get_value(handler)
        return value

    def get_value(self, handler):
        return self.clone(environ=handler.environ)

    def clone(self, *copy_properties, **set_properties):
        clone = type('', (), {})()
        clone.__class__ = self.__class__
        for prop_name in copy_properties:
            try:
                clone.__dict__[prop_name] = self.__dict__[prop_name]
            except KeyError:
                pass
        clone.__dict__.update(set_properties)
        return clone
