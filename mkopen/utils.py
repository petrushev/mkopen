from base64 import b64encode, b64decode
from binascii import unhexlify, hexlify

def uuid2b64(uuid):
    uuid_ = uuid.replace('-', '')
    b64 = b64encode(unhexlify(uuid_))
    return b64[:-2].replace('/', '_')

def b642uuid(b64):
    b64_ = b64.replace('_', '/') + '=='
    uuid = hexlify(b64decode(b64_))
    return uuid

def is_json(request):
    """
    Indicates if this request is JSON or not.  By default a request
    is considered to include JSON data if the mimetype is
    ``application/json`` or ``application/*+json``.

    .. versionadded:: 0.11
    """
    # TODO Should be removed once Flask upgrades to 0.11
    mt = request.mimetype
    if mt == 'application/json':
        return True
    if mt.startswith('application/') and mt.endswith('+json'):
        return True
    return False