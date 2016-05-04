from hashlib import md5

from sqlalchemy.sql.expression import func, literal
import chardet

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

    if tuple() in res:
        res.remove(tuple())

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

    @property
    def created(self):
        first_ = self.versions.order_by(Version.updated.asc()).first()
        if first_ is None:
            return None
        return first_.updated

    @property
    def modified(self):
        last_ver = self.last
        if last_ver is None:
            return None
        return last_ver.updated


class Version(BaseModel):

    def preview(self, length=1000):
        q = self.session(func.substring(Version.data, 1, length)\
                .filter(Version.id == self.id)).one()
        return q[0]

    def columns(self):
        if self.metadata.get('file_type') != 'csv':
            return None
        ver_id = self.id
        first_row = self.session.query(
            func.substring(
                Version.data, 1,
                func.position(literal('\n').op('in')(Version.data))))\
            .filter(Version.id == ver_id)\
            .one()[0]

        # try decoding
        first_row = str(first_row)
        encoding = chardet.detect(first_row)['encoding']
        if encoding is None:
            return None
        try:
            first_row = first_row.decode(encoding)
        except UnicodeDecodeError:
            return None

        columns = [col.strip(' \'"') for col in first_row.replace(';', ',').split(',')]
        return columns
