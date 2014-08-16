try:
    from urllib import parse
except ImportError:
    import urlparse as parse


def decoder(request):
    return dict(parse.parse_qsl(
        b''.join(request.input),
        keep_blank_values=True,
    ))
