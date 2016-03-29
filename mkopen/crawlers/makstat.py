# -*- coding: utf-8 -*-

#--------------- Завод за статистика -----------

import requests as rq
import json
from datetime import datetime
from time import sleep
from random import random

from mkopen.db.models import Data, Version, catalog2uuid, data2uuid

START_URL = 'http://makstat.stat.gov.mk/PXWeb/api/v1/mk/MakStat/'

CATALOG_PREFIX = u"Завод за статистика"
POST_BODY = json.dumps({
    "query": [],
    "response": {"format": "csv"}
})

TODAY = datetime.utcnow().date()

cat_descriptions = {}

def main(session):
    for item in rq.get(START_URL).json():
        process_item(session, item, tuple())

def process_item(session, item, top_cats):
    item_id = item['id']
    desc = item['text']
    if item['type'] == 'l':
        if item_id not in cat_descriptions:
            cat_descriptions[item_id] = desc
        crawl_subcat(session, item_id, desc, top_cats)

    else:
        crawl_file(session, item_id, desc, top_cats)

def crawl_subcat(session, cat_id, description, top_cats):
    cat_path = top_cats + (cat_id,)

    cat_url = START_URL + '/'.join(cat_path)
    q = rq.get(cat_url)
    try:
        data = q.json()
    except ValueError:
        return

    for item in data:
        process_item(session, item, cat_path)

def crawl_file(session, file_id, description, cat_path):
    # define catalog id
    cat_path_desc = [cat_descriptions[cat_id] for cat_id in cat_path]
    catalog_id = [CATALOG_PREFIX] + list(cat_path_desc)  + [description]

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

    # crawl data
    url = START_URL + '/'.join(cat_path + (file_id,))

    metadata = {
        'post_url': url,
        'category_api_url': START_URL + '/'.join(cat_path),
        'file_type': 'csv'
    }

    sleep(random() * 2 + 1.5)
    q = rq.post(url,
                headers={'Content-Type': 'application/json'},
                data=POST_BODY)
    if q.status_code != 200:
        print 'err', q.status_code, entry
        return

    data = q.content

    # check for changes
    data_hash = data2uuid(data)
    entry_version = Version.load(session, id=data_hash)

    if entry_version is None:
        # data is changed
        entry_version = Version(id=data_hash, data=data, updated=TODAY, metadata=metadata)
        entry_version.ref = entry

    elif entry_version.ref.id != entry.id:
        print 'data mistmatch:', entry_version.ref.id, entry.id

    # update entry for last check
    entry.last_checked = TODAY

    session.commit()
    session.expunge_all()
