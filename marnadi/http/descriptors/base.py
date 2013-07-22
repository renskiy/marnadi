import copy


class Descriptor(object):
    """Base class for managers.

    All custom managers should be inherited from this class.
    """

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.environ = None

    def __get__(self, owner_instance, owner_class):
        assert self.name, "descriptor must have 'name' property"
        clone = self.clone(environ=owner_instance.environ)
        setattr(owner_instance, self.name, clone)
        return clone

    def clone(self, **kwargs):
        clone = copy.deepcopy(self)
        clone.__dict__.update(kwargs)
        return clone