# -*- coding: utf-8 -*-

#---- Агрегатор, Државна комисија за спречување корупција -----

import csv
from StringIO import StringIO
from datetime import datetime

from mkopen.db.models import Data, Version, catalog2uuid, data2uuid
from mkopen.crawlers.dksk import CATALOG_PREFIX

AGG_CATALOG_ID = [CATALOG_PREFIX, u'Анкетни листови', u'Анкетни листови - сите']
AGG_METADATA = {
    'file_type': 'csv',
    'notes': ['non-primary']
}

TODAY = datetime.utcnow().date()
DATA_ID = catalog2uuid(AGG_CATALOG_ID)


def main(session):
    q = session.query(Data)\
               .filter(Data.catalog_id[1] == CATALOG_PREFIX,
                       Data.catalog_id != AGG_CATALOG_ID)\
               .order_by(Data.catalog_id[4]).all()

    writer_hnd = StringIO()
    writer_csv = csv.writer(writer_hnd)

    # prepare header
    writer_csv.writerow(
        u'Позиција,Институција,Име и презиме,Имот,Сопственост,Тип имот,Вредност,Карактеристика,Основ на стекнување'\
            .encode('utf-8').split(',')
    )

    for entry in q:
        extract_entry(writer_csv, entry)

    data = writer_hnd.getvalue()
    writer_hnd.close()

    save(session, data)

def extract_entry(writer_csv, entry):
    entry_version = entry.last
    if entry_version is None:
        return

    row_prefix = [cat.encode('utf-8') for cat in entry.catalog_id[1:]]

    reader_hnd = StringIO(entry_version.data)

    data_csv = csv.reader(reader_hnd)
    for row_id, row in enumerate(data_csv):
        # skip header
        if row_id == 0:
            continue

        full_row = row_prefix + row

        writer_csv.writerow(full_row)

    reader_hnd.close()
    entry.session.expunge(entry_version)

def save(session, data):
    entry = Data.load(session, id=DATA_ID)
    if entry is None:
        entry = Data(id=DATA_ID, catalog_id=AGG_CATALOG_ID, last_checked=TODAY)
        session.add(entry)
    else:
        entry.last_checked = TODAY

    data_hash = data2uuid(data)

    entry_version = Version.load(session, id=data_hash)
    if entry_version is None:
        entry_version = Version(id=data_hash, data=data, updated=TODAY, metadata=AGG_METADATA)
        entry_version.ref = entry

    session.commit()
