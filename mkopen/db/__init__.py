import warnings
from sys import stderr

from sqlalchemy.schema import MetaData
from sqlalchemy.orm import mapper, sessionmaker, clear_mappers
from sqlalchemy.orm.session import object_session
from sqlalchemy.exc import SAWarning

def reflect(engine, models, schema=None):
    metadata = MetaData()
    metadata.bind = engine

    # reflection of db structure
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=SAWarning)
        metadata.reflect(schema=schema, views=False)

    if schema is not None:
        tables = dict((table_name.replace(str(schema) + ".", ""), table)
                      for table_name, table in metadata.tables.iteritems())
    else:
        tables = metadata.tables

    clear_mappers()

    mappers = {}
    for table_name, table in tables.iteritems():
        modelname = "".join([word.capitalize() for word in table_name.split("_")])

        try:
            model = getattr(models, modelname)
        except AttributeError:
            stderr.write("Missing model for table %s\n" % table_name)
        else:
            mappers[modelname] = mapper(model, table)

    Session = sessionmaker(bind=engine, autocommit=False, autoflush=True)

    return mappers, tables, Session

class BaseModel(object):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def session(self):
        return object_session(self)

    def drop(self):
        self.session.delete(self)

    @classmethod
    def load(cls, session, **kwargs):
        q = session.query(cls)
        for key, val in kwargs.items():
            field = getattr(cls, key)
            q = q.filter(field == val)
        return q.first()

    def __repr__(self):
        cls = self.__class__
        class_name = cls.__name__
        session = self.session
        if session is None:
            return '<%s [not persisted]>' % class_name

        primary_key_columns = session.__class__.mappers[class_name].primary_key
        pk_attrs = ', '.join('%s:%s' % (key.name, getattr(self, key.name))
                             for key in primary_key_columns)
        return '<%s : %s>' % (class_name, pk_attrs)
