# -*- coding: utf-8 -*-

#---------- Државна комисија за спречување корупција ----------

import requests as rq
from StringIO import StringIO
import csv
from datetime import datetime
from time import sleep
from random import random
import locale

from lxml.html import fromstring

from mkopen.db.models import Data, Version, catalog2uuid, data2uuid
from mkopen.utils import setlocale

TODAY = datetime.utcnow().date()
CATALOG_PREFIX = u"Државна комисија за спречување корупција"
BASE = 'http://www.dksk.org.mk/imoti_2'

def main(session):

    cur_page = 1

    final_page = False
    collected_catalogs = []

    while not final_page:
        start = BASE + '/index.php?search=%d' % cur_page
        print 'page:', cur_page

        sleep(random() * 0.5 + 0.5)
        content = rq.get(start).content
        doc = fromstring(content)

        # get links to detail pages
        detail_a = doc.cssselect("a[href^=detail\.php]")

        for link in detail_a:
            url = BASE + '/' + link.attrib['href']

            catalog, content = crawl_details(url)

            if catalog is not None and content is not None:
                collected_catalogs.append(','.join(reversed(catalog)))
                catalog = (CATALOG_PREFIX, ) + catalog
                metadata = {'url': url,
                            'page_url': start,
                            'file_type': 'csv'}
                save(session, catalog, content, metadata)

        # check if final page
        next_ = doc.cssselect("img[src='img/forward.png']")

        final_page = (len(next_) == 0)
        cur_page = cur_page +  1

    with setlocale():
        collected_catalogs.sort(cmp=locale.strcoll)

    # save active pages
    catalog = (CATALOG_PREFIX, u'Анкетни листови', u'Активни')
    content = ('\n'.join(collected_catalogs)).encode('utf-8')
    metadata = {'file_type': 'csv'}
    save(session, catalog, content, metadata)

def crawl_details(url):

    sleep(random() * 0.5 + 0.5)
    content = rq.get(url).content
    doc = fromstring(content)
    tables = doc.cssselect('table.class')

    if len(tables) < 2:
        # no details
        return None, None

    definer_table, details_table = tables[0], tables[1]

    tr = definer_table.cssselect('tr')[1]
    definer = [td.text_content().strip() for td in tr.cssselect('td')]
    definer = (definer[2], definer[3], definer[0] + ' ' + definer[1])

    csv_handle = StringIO()
    writer = csv.writer(csv_handle)

    for tr in details_table.cssselect('tr'):
        line = [td.text_content().strip().encode('utf-8')
                for td in tr.cssselect('td')]

        writer.writerow(line)

    csv_content = csv_handle.getvalue()
    csv_handle.close()

    # resort data
    csv_content = csv_content.split('\n')
    csv_header = csv_content.pop(0)
    csv_content.sort()
    csv_content.insert(0, csv_header)
    csv_content = '\n'.join(csv_content)

    return definer, csv_content

def save(session, catalog_id, data, metadata):
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
        metadata = dict(metadata)
        metadata['file_type'] = 'csv'
        entry_version = Version(id=data_hash, data=data, updated=TODAY, metadata=metadata)
        entry_version.ref = entry

    elif entry_version.ref.id != entry.id:
        print 'data mistmatch:', entry_version.ref.id, entry.id

    # update entry for last check
    entry.last_checked = TODAY

    session.commit()

    return entry_version
