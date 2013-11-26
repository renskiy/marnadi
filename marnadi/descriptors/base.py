from copy import copy


class Descriptor(object):
    """Base class for managers.

    All custom managers should be inherited from this class.
    """

    def __init__(self):
        self.attr_name = None
        self.environ = None

    def __get__(self, handler, handler_class):
        if handler is None:
            return self  # static access
        assert self.attr_name, "Descriptor need not empty `attr_name`"
        value = self.get_value(handler)
        setattr(handler, self.attr_name, value)
        return value

    def get_value(self, handler):
        value = copy(self)
        value.environ = handler.environ
        return value