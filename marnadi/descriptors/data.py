from marnadi import errors
from marnadi.descriptors import Descriptor


class Data(Descriptor):

    def __init__(self, *content_decoders, **kwargs):
        super(Data, self).__init__(**kwargs)
        # TODO may contain strings or modules
        # TODO replace strings by modules once they have been loaded
        self.content_decoders = dict(content_decoders)
        self.headers = None
        self._decoded_data = None

    def __str__(self):
        return self.data

    def clone(self, owner_instance):
        instance = super(Data, self).clone(owner_instance)
        instance.content_decoders = self.content_decoders
        instance.headers = owner_instance.headers
        instance._decoded_data = None
        return instance

    @property
    def data(self):
        if self._decoded_data is None:
            self._decoded_data = self.decode_request_data()
        return self._decoded_data

    def decode_request_data(self):
        try:
            content_length = int(self.headers['Content-Length'])
        except TypeError:
            raise errors.HttpError(errors.HTTP_400_BAD_REQUEST)
        except KeyError:
            if self.environ.request_method in ('POST', 'PUT'):
                raise errors.HttpError(errors.HTTP_411_LENGTH_REQUIRED)
            content_length = 0
        if content_length == 0:
            return ''
        content_type, content_params = self.headers.get_splitted('Content-Type')
        decode = self.get_decoder(content_type)
        content = self.environ['wsgi.input'].read(content_length)
        return decode(content, **content_params)

    @staticmethod
    def plain_text_decoder(content, **kwargs):
        return content

    def get_decoder(self, content_type):
        if content_type not in self.content_decoders:
            return self.plain_text_decoder