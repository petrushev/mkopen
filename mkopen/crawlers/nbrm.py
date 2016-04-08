# -*- coding: utf-8 -*-
from datetime import datetime
from time import sleep
from random import random

import requests as rq
from lxml.html import fromstring
from werkzeug.urls import url_unquote

from mkopen.db.models import catalog2uuid, data2uuid, Data, Version

CATALOG_PREFIX = u'Народна банка'
TODAY = datetime.utcnow().date()


def main(session):
    search_url = 'http://www.nbrm.mk/default.aspx?pSearch=xlsx'
    q = rq.get(search_url)
    doc = fromstring(q.content)
    doc.make_links_absolute(search_url)
    for link in doc.cssselect('a.search_results'):
        for section, title, url in crawl_page(link.attrib['href']):
            save(session, section, title, url)

def crawl_page(url):
    sleep(random() + 0.5)
    q = rq.get(url)
    doc = fromstring(q.content)
    doc.make_links_absolute(url)

    section_title = doc.cssselect('#ArticleTitle')
    if len(section_title) == 0:
        section_title = None
    else:
        section_title = section_title[0].text_content().strip()

    for link in doc.cssselect("a[href]"):
        x_url = link.attrib['href']
        if not x_url.endswith('.xlsx'):
            continue

        doc_title = x_url.split('/')[-1][:-5]
        doc_title = url_unquote(doc_title).replace('_', ' ').replace('WebBuilder', '').strip()
        yield section_title, doc_title, url

def save(session, section, title, url):
    if section is None:
        catalog_id = [CATALOG_PREFIX, title]
    else:
        catalog_id = [CATALOG_PREFIX, section, title]
    data_id = catalog2uuid(catalog_id)
    entry = Data.load(session, id=data_id)
    if entry is None:
        entry = Data(id=data_id, last_checked=TODAY, catalog_id=catalog_id)
        session.add(entry)
    elif entry.last_checked == TODAY:
        print 'skip:', entry.id
        return

    # crawl doc
    sleep(random() + 0.5)
    q = rq.get(url)
    if q.status_code != 200:
        print 'err:', q.status_code, url
        return

    entry.last_checked = TODAY

    content = q.content
    data_hash = data2uuid(content)
    metadata = {'url': url, 'file_type': 'xlsx'}

    version = Version.load(session, id=data_hash)
    if version is None:
        version = Version(id=data_hash, data=content, updated=TODAY, metadata=metadata)
        version.ref = entry
    elif version.ref.id != entry.id:
        print 'data mistmatch:', version.ref.id, entry.id

    session.commit()
    session.expunge_all()
