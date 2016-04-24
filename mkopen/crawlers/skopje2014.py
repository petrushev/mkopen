# -*- coding: utf-8 -*-

#---------- Призма / Скопје 2014 ----------

from StringIO import StringIO
import csv
from datetime import datetime
from time import sleep
from random import random

import requests as rq
from lxml.html import fromstring

from mkopen.db.models import Data, Version, catalog2uuid, data2uuid

TODAY = datetime.utcnow().date()
CATALOG_PREFIX = (u"Призма", u"Скопје 2014")

INVESTORS = '1,19,30,34,26,2,3,36,25,21,32,28,38,4,39,27,29,5,35,33,31,23,20,17,22,16,18,6,24,7,9,8'
INVESTORS = set(map(int, INVESTORS.split(',')))

METADATA = {'file_type': 'csv',
            'url': 'http://skopje2014.prizma.birn.eu.com'}

def main(session):
    csv1_handle = StringIO()
    csv2_handle = StringIO()
    writer1 = csv.writer(csv1_handle)
    writer2 = csv.writer(csv2_handle)

    writer1.writerow(u'Инвеститор,Вид изведувач,Изведувач,Вредност (ден.)'.encode('utf-8').split(','))
    writer2.writerow(u'Инвеститор,Објект,Вредност (ден.)'.encode('utf-8').split(','))

    for inv in list(INVESTORS):
        crawl(inv, writer1, writer2)

    data1 = csv1_handle.getvalue().strip()
    csv1_handle.close()
    data2 = csv2_handle.getvalue().strip()
    csv2_handle.close()

    data1 = resort(data1)
    data2 = resort(data2)

    save(session, data1, data2)

    session.commit()


def crawl(inv, writer1, writer2):
    sleep(random() + 0.5)

    url = 'http://skopje2014.prizma.birn.eu.com/mk/rezultati/inv=%d' % inv
    content = rq.get(url).content.decode('utf-8')
    doc = fromstring(content)

    investor = doc.cssselect('ul#ulInvestitori')[0].cssselect('li')[0].text_content().strip()

    contractors_table = doc.cssselect('table#tblIzveduvaci')[0]
    for tr in contractors_table.cssselect('tr'):
        tds = [td.text_content() for td in tr.cssselect('td')]
        if tds == []: continue
        contractor_ = tds[1].split('(')
        contractor_group = contractor_.pop(len(contractor_) - 1)
        contractor = '('.join(contractor_)
        contractor = contractor.strip()
        contractor_group = contractor_group.strip(' )')

        val = tds[3].replace(u'ден', '').replace('.', '').strip()
        line = [investor, contractor_group, contractor, val]
        writer1.writerow([item.encode('utf-8') for item in line])

    objects_table = doc.cssselect('table#tblObjekti')[0]
    for tr in objects_table.cssselect('tr'):
        tds = [td.text_content() for td in tr.cssselect('td')]
        if tds == []: continue
        object_ = tds[1].strip()
        val = tds[3].replace(u'ден', '').replace('.', '').strip()
        line = [investor, object_, val]
        writer2.writerow([item.encode('utf-8') for item in line])

def resort(data):
    lines = data.split('\n')
    header = lines.pop(0)
    lines.sort()
    lines.insert(0, header)
    data_ = '\n'.join(lines)
    return data_

def save(session, data1, data2):
    catalog = CATALOG_PREFIX + (u'Инвеститори и изведувачи',)
    save_catalog(session, catalog, data1)

    catalog = CATALOG_PREFIX + (u'Инвеститори и објекти',)
    save_catalog(session, catalog, data2)

def save_catalog(session, catalog, data):
    entry = Data.load(session, catalog_id=catalog)
    if entry is None:
        id_ = catalog2uuid(catalog)
        entry = Data(id=id_, catalog_id=catalog, last_checked=TODAY)
        session.add(entry)
    else:
        entry.last_checked = TODAY

    data_hash = data2uuid(data)
    ver = Version.load(session, id=data_hash)
    if ver is not None:
        return

    ver = Version(id=data_hash, updated=TODAY, data=data, metadata=METADATA)
    ver.ref = entry
    session.flush()


if __name__ == '__main__':
    main(None)
