try:
    from urllib import parse
except ImportError:
    import urlparse as parse


def decoder(request):
    return parse.parse_qs(
        b''.join(request.input),
        keep_blank_values=True,
    )
