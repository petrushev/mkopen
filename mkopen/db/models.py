from hashlib import md5

from mkopen.db import BaseModel


def catalog2uuid(catalog_id):
    catalog_id_ = '/'.join(catalog_id).encode('utf-8')
    return md5(catalog_id_).hexdigest()

def data2uuid(data):
    return md5(data).hexdigest()

def combine_catalogs(catalogs):
    res = set()
    for catalog in catalogs:
        for end in range(len(catalog) + 1):
            part_catalog = catalog[:end]
            res.add(part_catalog)

    res = list(res)
    res.sort(key=len)
    return res


class Data(BaseModel):

    @property
    def last(self):
        return self.versions.order_by(Version.updated.desc()).first()

    @property
    def filename(self):
        return self.catalog_id[-1]


class Version(BaseModel):
    pass
