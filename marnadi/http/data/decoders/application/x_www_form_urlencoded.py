try:
    from urllib import parse
except ImportError:
    import urlparse as parse


def decoder(request):
    return dict(parse.parse_qsl(
        request.input.read(request.content_length).decode(
            encoding=request.content_type.get('charset', 'utf-8')
        ),
        keep_blank_values=True,
    ))
