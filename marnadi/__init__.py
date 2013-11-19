def byte_str(obj):
    return str(bytearray(unicode(obj or ''), 'utf-8'))