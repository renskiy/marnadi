import copy


class ManagerProcessor(type):

    def __new__(mcs, name, bases, attributes):
        cls = super(ManagerProcessor, mcs).__new__(mcs, name, bases, attributes)
        for attr_name, attr_value in attributes.iteritems():
            cls.set_manager_name(attr_value, attr_name)
        return cls

    def __setattr__(cls, attr_name, attr_value):
        super(ManagerProcessor, cls).__setattr__(attr_name, attr_value)
        cls.set_manager_name(attr_value, attr_name)

    def set_manager_name(cls, manager, name):
        if isinstance(manager, AbstractManager):
            manager.name = manager.name or name
            for attr_name, attr_value \
                    in manager.__class__.__dict__.iteritems():
                cls.set_manager_name(attr_value, attr_name)


class AbstractManager(object):

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.environ = None

    def __get__(self, owner, owner_class):
        clone = self.clone(environ=owner.environ)
        assert self.name, "manager can't be without 'name'"
        setattr(owner, self.name, clone)
        return clone

    def clone(self, **kwargs):
        clone = copy.deepcopy(self)
        clone.__dict__.update(kwargs)
        return clone


class Manager(AbstractManager):
    """Base class for all handler's managers.

    Custom managers should inherit this functionality.

    Attributes:
        name: attribute name of owner class to which this manager assigned.
        environ: Environ class object containing environment variables of
        current request.
    """

    __metaclass__ = ManagerProcessor
