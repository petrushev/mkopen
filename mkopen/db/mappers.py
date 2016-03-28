from sqlalchemy.engine import create_engine
from sqlalchemy.orm import relationship, backref

from mkopen.db import models, reflect

def sessionmaker(dbconfig):
    dbconfig = dbconfig.copy()
    conn_str = dbconfig.pop('url')
    if 'schema' in dbconfig:
        schema = dbconfig.pop('schema')
    else:
        schema = None

    engine = create_engine(conn_str, **dbconfig)
    mappers, _tables, Session = reflect(engine, models, schema)

    # add mapper relationships
    mappers['Data'].add_properties({
        'versions': relationship(models.Version,
                                 lazy='dynamic',
                                 order_by=models.Version.updated.desc(),
                                 backref=backref('ref',
                                                 lazy='joined'))
    })

    Session.class_.mappers = mappers

    return Session
