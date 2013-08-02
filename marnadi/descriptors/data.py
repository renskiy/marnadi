from marnadi.descriptors import Descriptor


class Data(Descriptor):
    # TODO finish implementation

    content_decoders = {
        'multipart/form-data': 'marnadi.mime.multipart.form_data',
        'application/json': 'marnadi.mime.application.json',
        'application/x-www-form-urlencoded':
            'marnadi.mime.application.x_www_form_urlencoded',
    }

    def __init__(self, *content_decoders, **kwargs):
        super(Data, self).__init__(**kwargs)
        self.content_decoders.update(content_decoders)