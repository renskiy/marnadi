try:
    from urllib import parse
except ImportError:
    import urlparse as parse


def decoder(request):
    encoding = request.content_type.params.get('charset', 'utf-8')
    return dict(parse.parse_qsl(
        request.input.read(request.content_length).decode(encoding=encoding),
        keep_blank_values=True,
    ))
