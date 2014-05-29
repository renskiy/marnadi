from copy import copy


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
        value = copy(self)
        value.environ = handler.environ
        return value