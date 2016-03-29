from base64 import b64encode, b64decode
from binascii import unhexlify, hexlify

from werkzeug.urls import url_encode

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


class SearchQuery(object):

    def __init__(self, query=''):
        self._parsed = {}
        for item in query.split('&'):
            if '=' in item:
                item = item.split('=')
                self._parsed[item[0]] = item[1]

    def copy(self):
        q = SearchQuery()
        q._parsed = dict(self._parsed)
        return q

    def __str__(self):
        return url_encode(self._parsed)

    def set(self, key, val):
        q = self.copy()
        q._parsed[key] = val
        return q

    def delete(self, key):
        q = self.copy()
        if key in q._parsed:
            del q._parsed[key]
        return q
