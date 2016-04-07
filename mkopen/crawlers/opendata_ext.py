# -*- coding: utf-8 -*-
from urlparse import urlparse
from datetime import datetime
from time import sleep
from random import random

import requests as rq
import chardet
from lxml.html import fromstring
from lxml.etree import ParserError

from mkopen.db.models import catalog2uuid, data2uuid, Data, Version

CATALOG_PREFIX = u'Отворени податоци .gov.mk (екстерни)'
TODAY = datetime.utcnow().date()


def main(session):
    url = 'http://ogdi.otvorenipodatoci.gov.mk/DataCatalog/DataSets'
    page = 1

    while True:
        print 'page:', page

        q = rq.post(url,
                    data={'pageSize': '50', 'pageNumber': str(page),
                          'orderField': 'Name', 'orderType': 'Asc', 'filter': 'null'})
        sleep(random() / 2 + 1.5)
        content = q.content
        encoding = chardet.detect(content)['encoding']
        content = content.decode(encoding)

        try:
            doc = fromstring(content)
        except ParserError:
            break

        for doc_title, source, new_url, content in parse(url, doc):
            print doc_title, source, len(content), new_url
            save(session, doc_title, source, new_url, content)

        page = page + 1


def parse(url, doc):
    doc.make_links_absolute(url)
    for tr in doc.cssselect('tr'):
        link = tr.cssselect('a[href]')
        if len(link) == 0:
            continue
        link = link[0]
        doc_title = link.text_content().strip()
        url = link.attrib['href']
        source = tr.cssselect('td')[2].text_content().strip()

        sleep(random() / 2 + 1.5)
        q = rq.get(url, allow_redirects=False)
        doc = fromstring(q.content)
        parts = doc.cssselect('div.data-set-default-container-wrapper')
        extern_div = list(parts[0])[1]

        # check if external link exist
        if extern_div.attrib['class'] == 'box-label-wrapper':
            link = extern_div.cssselect('a[href]')
            if len(link) > 0:
                new_url = link[0].attrib['href']

                q = rq.get(new_url, allow_redirects=False)
                if q.status_code == 200:
                    content = q.content

                    yield doc_title, source, new_url, content

def save(session, doc_title, source, new_url, content):
    catalog_id = [CATALOG_PREFIX, source, doc_title]
    data_id = catalog2uuid(catalog_id)

    metadata = {
        'url': new_url
    }

    url_path = urlparse(new_url).path.split('.')
    if len(url_path) > 1:
        metadata['file_type'] = url_path[-1]

    entry = Data.load(session, id=data_id)
    if entry is None:
        entry = Data(id=data_id, catalog_id=catalog_id, last_checked=TODAY)
        session.add(entry)
    else:
        entry.last_checked = TODAY

    data_hash = data2uuid(content)
    entry_version = Version.load(session, id=data_hash)
    if entry_version is None:
        entry_version = Version(id=data_hash, data=content,
                                updated=TODAY, metadata=metadata)
        entry_version.ref = entry
    elif entry_version.ref.id != entry.id:
        print 'data mistmatch:', entry_version.ref.id, entry.id

    session.commit()
    session.expunge_all()


if __name__ == '__main__':
    main(None)
