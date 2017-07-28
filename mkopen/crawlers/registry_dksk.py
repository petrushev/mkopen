# -*- coding: utf-8 -*-

#---------- Регистар на избрани и именувани лица, ДКСК ----------

import requests as rq
from datetime import datetime
from time import sleep
from random import random
import locale
import json

from mkopen.db.models import Data, Version, catalog2uuid, data2uuid
from mkopen.utils import setlocale

TODAY = datetime.utcnow().date()
CATALOG_PREFIX = u"Регистар на избрани и именувани лица, ДКСК"
BASE_URL = "https://register.dksk.org.mk/Public/GetAllSubmissions"
PER_PAGE = 20


def main(session):
    page = 0

    active = []

    while True:
        page = page + 1
        print 'crawling page {0}...'.format(page)

        q = rq.post(
            BASE_URL,
            headers={
                'Content-Type': 'application/json'},
            data=json.dumps({
                'page': page,
                'rows': PER_PAGE,
                'searchText': '',
                'institutionId': None,
                'workingPositionId': None,
                'electedUser': True,
                'terminateElectedUser': False,}),
            timeout=3,
        )
        sleep(random() * 0.5 + 0.5)


        data = q.json()['submissions']

        if len(data) == 0:
            break

        for item in data:
            catalog_id, compiled_data = compile_data(item)
            save(session, catalog_id, compiled_data)

            active_row = u','.join((catalog_id[1:])[::-1])
            active.append(active_row)

    # save active
    with setlocale():
        active.sort(cmp=locale.strcoll)

    # save active pages
    catalog = (CATALOG_PREFIX, u'Регистар', u'Активни')
    content = ('\n'.join(active)).encode('utf-8')
    save(session, catalog, content)


def compile_data(item):

    position = item['WorkingPosition']['Position']
    institution = item['Institution']['Name']

    rows = [
        (u'Име', item['FirstName']),
        (u'Презиме', item['LastName']),
        (u'Email', item['Email']),
        (u'Позиција', position),
        (u'Институција, име', institution),
        (u'Институција, општина',
            u'{0}, {1}'.format(
                item['Institution']['Municipality']['Name'].strip(),
                item['Institution']['Municipality']['City']['Name'].lstrip())),
    ]

    if item.get('Citizenship') is not None:
        rows.append((u'Државјанство', item['Citizenship']['Name']))
    if item.get('EducationDegree') is not None:
        rows.append((u'Образование, ниво', item['EducationDegree']['Degree']))
    if item.get('EducationType') is not None:
        rows.append((u'Образование, тип', item['EducationType']['Type']))
    if item.get('Nationality') is not None:
        rows.append((u'Националност', item['Nationality']['Name']))

    rows.extend([
        #(u'ЕМБГ', item['Embg']),
        #(u'Адреса', item['Address']),
        #(u'Телефон', item['PhoneNumber']),
        (u'Број на акт', item['ActNumber']),
        (u'Број на анкетен лист', item['AssetDeclarationId']),
        (u'Број на документ', item['DocumentNumber']),
        (u'Коментар', item['Comment']),
        (u'Оригинална референца', item['Id']),
        (u'Институција, оригинална референца', item['Institution']['Id']),
    ])

    data = u''
    for key, val in rows:
        if val is None:
            val = ''
        row = u'{0:40}: {1}'.format(key, val)
        row = row.replace('\n', ' ')
        data = data + row + '\n'

    fullname = u'{0} {1}'.format(item['FirstName'], item['LastName'])
    catalog_id = (CATALOG_PREFIX, position, institution.title(), fullname)

    return catalog_id, data.encode('utf-8')


def save(session, catalog_id, data):
    # locate entry
    data_id = catalog2uuid(catalog_id)
    entry = Data.load(session, id=data_id)

    if entry is None:
        entry = Data(id=data_id, catalog_id=catalog_id, last_checked=TODAY)
        session.add(entry)

    elif entry.last_checked == TODAY:
        # data is crawled and recently checked
        print 'skip:' , entry
        return

    # check for changes
    data_hash = data2uuid(data)
    entry_version = Version.load(session, id=data_hash)

    if entry_version is None:
        # data is changed
        metadata = dict(file_type='text')
        entry_version = Version(id=data_hash, data=data, updated=TODAY, metadata=metadata)
        entry_version.ref = entry

    elif entry_version.ref.id != entry.id:
        print 'data mistmatch:', entry_version.ref.id, entry.id

    # update entry for last check
    entry.last_checked = TODAY

    session.commit()

