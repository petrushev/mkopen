from hashlib import md5

from mkopen.db import BaseModel

def catalog2uuid(catalog_id):
    catalog_id_ = '/'.join(catalog_id).encode('utf-8')
    return md5(catalog_id_).hexdigest()

def data2uuid(data):
    return md5(data).hexdigest()


class Data(BaseModel):
    pass


class Version(BaseModel):
    pass
