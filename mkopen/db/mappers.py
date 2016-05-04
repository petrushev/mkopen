from sqlalchemy.engine import create_engine
from sqlalchemy.orm import relationship, backref, deferred

from mkopen.db import models, reflect

def sessionmaker(dbconfig):
    dbconfig = dbconfig.copy()
    conn_str = dbconfig.pop('url')
    if 'schema' in dbconfig:
        schema = dbconfig.pop('schema')
    else:
        schema = None

    engine = create_engine(conn_str, **dbconfig)
    mappers, tables, Session = reflect(engine, models, schema)

    # add mapper relationships
    mappers['Data'].add_properties({
        'versions': relationship(models.Version,
                                 lazy='dynamic',
                                 backref=backref('ref',
                                                 lazy='joined'))
    })

    mappers['Version'].add_properties({
        'data': deferred(tables['version'].c['data'])
    })

    Session.class_.mappers = mappers

    return Session
