from base64 import b64encode, b64decode
from binascii import unhexlify, hexlify
import difflib
import locale
import threading
from contextlib import contextmanager


from werkzeug.urls import url_encode
import chardet


diff_fc = difflib.HtmlDiff(wrapcolumn=60).make_table


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


def compare(data_1, data_2):
    enc_1 = chardet.detect(data_1)['encoding']
    enc_2 = chardet.detect(data_2)['encoding']
    if enc_1 is None and enc_2 is None:
        # TODO check for pdf
        return None
    if enc_1 is None or enc_2 is None:
        # only one is binary
        return None

    try:
        udata_1 = data_1.decode(enc_1)
        udata_2 = data_2.decode(enc_2)
    except UnicodeDecodeError:
        # detected encodings did not work
        return None

    udata_1 = udata_1.split('\n')
    udata_2 = udata_2.split('\n')

    return diff_fc(udata_1, udata_2, context=True, numlines=2)

LOCALE_LOCK = threading.Lock()

@contextmanager
def setlocale(name='mk_MK.UTF-8', locale_part=locale.LC_ALL):
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)

def date_format(date_, format_='%d %B, %Y', locale_name='mk_MK.UTF-8'):
    with setlocale(locale_name):
        formated = date_.strftime(format_).decode('utf-8')
    return formated

def file_size_format(size):
    if size < 1024:
        return '%d B' % size
    size = size * 1.0 / 1024
    if size < 1024:
        return '%.02f KB' % size
    size = size / 1024
    return '%.02f MB' % size


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

    @property
    def empty(self):
        return len(self._parsed) > 0
