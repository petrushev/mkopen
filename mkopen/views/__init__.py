# -*- coding: utf-8 -*-
import json
from os import environ
from itertools import groupby
from operator import itemgetter

from flask.views import View
from flask.helpers import make_response
from flask.templating import render_template
from flask import current_app, request, g
from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.wrappers import Response
from werkzeug.utils import redirect
from werkzeug.urls import url_quote_plus, url_quote
from sqlalchemy.sql.operators import op
from sqlalchemy.sql.expression import func, and_
import chardet

from mkopen.db.models import Version, Data, combine_catalogs
from mkopen.utils import b642uuid, SearchQuery, compare2, uuid2b64

from mkopen.crawlers.dksk import CATALOG_PREFIX as DKSK_CAT
from mkopen.crawlers.opendata import CATALOG_PREFIX as OPENDATA_CAT
from mkopen.crawlers.opendata_ext import CATALOG_PREFIX as OPENDATAEXT_CAT
from mkopen.crawlers.skopje2014 import CATALOG_PREFIX as PRIZMA_CAT
from mkopen.crawlers.registry_dksk import CATALOG_PREFIX as REGISTRY_CAT

GOOGLE_WEBMASTER = environ.get('GOOGLE_WEBMASTER', None)
GOOGLE_WEBMASTER_HTTP = environ.get('GOOGLE_WEBMASTER_HTTP', None)

ROBOTS = """
User-agent: *
Disallow: /download/*
Disallow: /diff/*
"""
CATALOGS = (DKSK_CAT, u"Завод за статистика", OPENDATA_CAT, REGISTRY_CAT, OPENDATAEXT_CAT, PRIZMA_CAT[0])

catalog_id_getter = lambda item: tuple(item[0].catalog_id[:-1])
itemgetter0, itemgetter1 = itemgetter(0), itemgetter(1)


class ActionView(View):

    methods = ['GET']

    def __init__(self, action, is_json=False):
        self.action = action
        self.is_json = is_json
        q = SearchQuery()
        for k, v in request.args.items():
            q = q.set(k, v)
        self.view = {'url_query': q,
                     'path': request.path,
                     'base_url': request.host_url.rstrip('/')}

    def dispatch_request(self, *args, **kwargs):
        action_fc = getattr(self, self.action, None)
        if action_fc is None:
            return Response('Not found', 404)

        result = action_fc(*args, **kwargs)

        result = self.post_process(result)

        return result

    def post_process(self, result):
        if self.is_json:
            if isinstance(result, dict):
                result = json.dumps(result)
            result = make_response(result)
            result.headers['Content-Type'] = 'application/json'

        return result


class IndexView(ActionView):

    def index(self):
        sq = g.dbsession.query(Version.data_id, Version.updated,
                               func.max(Version.updated).over(partition_by=Version.data_id)\
                                   .label('max_updated'))\
              .subquery()

        q = g.dbsession.query(Data, sq.c.updated)\
             .join((sq, and_(sq.c.data_id == Data.id,
                             sq.c.updated == sq.c.max_updated)))\

        q = q.order_by(sq.c.updated.desc(), Data.catalog_id)\
             .limit(15)

        data = q.all()

        data.sort(key=catalog_id_getter)

        data2 = [(catalog_id,
                  map(itemgetter0, sorted(catalog_data, key=itemgetter1, reverse=True)))
            for catalog_id, catalog_data in groupby(data, key=catalog_id_getter)]

        if request.scheme == 'https':
            google_webmaster = GOOGLE_WEBMASTER
        elif request.scheme == 'http':
            google_webmaster = GOOGLE_WEBMASTER_HTTP
        else:
            google_webmaster = None

        # stats
        total_datasets = g.dbsession.query(func.count(Data.id)).one()[0]
        last_update = g.dbsession.query(func.max(Version.updated)).one()[0]

        self.view.update({'data': data2,
                          'google_webmaster_verifier': google_webmaster,
                          'catalogs': CATALOGS,
                          'query': None,
                          'catalog': None,
                          'total_datasets': total_datasets,
                          'last_update': last_update})

        return render_template('index.html', **self.view)

    def robots(self):
        return Response(ROBOTS.lstrip(), content_type='text/plain', status=200)


class SearchView(ActionView):

    def index(self):
        query, catalog = None, None
        if 'search' in request.args:
            query = request.args['search'].strip()
            if query == '':
                query = None
        if 'catalog' in request.args:
            catalog = request.args['catalog'].strip()
            if catalog == '':
                catalog = None

        if query is not None:
            url = '/search/' + url_quote(query)
            if catalog is not None:
                url = url + '?catalog=' + url_quote(catalog)
            return redirect(url, 301)

        if catalog is not None:
            url = '/catalog/' + catalog
            #url = '/catalog/' + '/'.join(map(url_quote_plus, catalog.split('/')))
            return redirect(url, 301)

        return redirect('/', 302)

    def search(self, query):
        catalog = None
        if 'catalog' in request.args:
            catalog = request.args['catalog'].strip()
            if catalog == '':
                catalog = None

        return self._search(query, catalog)

    def catalog(self, catalog_id):
        return self._search(None, catalog_id)

    def _search(self, query, catalog):
        # build filters
        filters = []

        if query is not None:
            for query_part in query.split(' '):
                if query_part == '':
                    continue
                query_filter = func.join_text_array(Data.catalog_id, ' ')\
                                   .ilike('%%%s%%' % query_part)
                filters.append(query_filter)

        if catalog is not None:
            catalog_filter = catalog.split('/')

            filters.append(Data.catalog_id.op('@>')(catalog_filter))
            catalog_depth = len(catalog_filter)
        else:
            catalog_depth = 1

        # redirect if empty search
        if filters == []:
            return redirect('/', 302)

        # look for catalogs
        cat_q = g.dbsession.query((Data.catalog_id[ 1 : func.least(func.array_length(Data.catalog_id, 1) - 1, catalog_depth + 1) ]).distinct())\
                 .filter(*filters).all()
        cat_q = map(tuple, map(itemgetter0, cat_q))

        catalogs = combine_catalogs(cat_q)

        # query data with the last version as sort key
        sq = g.dbsession.query(Version.data_id, Version.updated,
                               func.max(Version.updated).over(partition_by=Version.data_id)\
                                   .label('max_updated'))\
              .subquery()

        q = g.dbsession.query(Data, sq.c.updated)\
             .join((sq, and_(sq.c.data_id == Data.id,
                             sq.c.updated == sq.c.max_updated)))\
             .filter(*filters)

        q = q.order_by(sq.c.updated.desc(), Data.catalog_id)

        # pagination
        try:
            page = int(request.args['page'])
        except (ValueError, BadRequest):
            page = 1
        offset = (page - 1) * 15

        data = q.offset(offset).limit(16).all()

        final_page = (len(data) != 16)

        # check for single result
        if page == 1 and len(data) == 1:
            entry = data[0][0]
            return redirect('/entry/' + uuid2b64(entry.id))

        data = data[:15]

        # group by catalog
        data.sort(key=catalog_id_getter)

        data2 = [(catalog_id,
                  map(itemgetter0, sorted(catalog_data, key=itemgetter1, reverse=True)))
            for catalog_id, catalog_data in groupby(data, key=catalog_id_getter)]

        self.view.update({'data': data2,
                          'page': page,
                          'final_page': final_page,
                          'catalogs': catalogs,
                          'query': query})
        if catalog is not None:
            self.view['catalog'] = catalog.split('/')

        return render_template('search.html', **self.view)


class EntryView(ActionView):

    def index(self, data_b64):
        uuid = b642uuid(data_b64)
        entry = Data.load(g.dbsession, id=uuid)

        versions = entry.versions.order_by(Version.updated.desc()).all()

        # load preview
        last = versions[0]
        preview_data, is_preview_full = self._load_preview(last)
        if preview_data is not None:
            self.view.update({'preview': preview_data,
                              'is_preview_full': is_preview_full})

        self.view.update({'entry': entry, 'versions': versions})

        return render_template('entry.html', **self.view)

    def _load_preview(self, version):
        if version.metadata['file_type'] not in ('csv', 'text'):
            return None, None

        preview_data = g.dbsession.query(func.substring(Version.data, 1, 18000),
                                         func.length(Version.data))\
                        .filter(Version.id==version.id).one()
        preview_data, version_length = preview_data
        preview_data = str(preview_data)

        is_preview_full = ( len(preview_data) == version_length )

        if not is_preview_full:
            try:
                last_return = preview_data.rindex('\n')
            except ValueError:
                # too long preview
                return None, None
            preview_data = preview_data[:last_return]

        encoding = chardet.detect(preview_data)['encoding']
        if encoding is None:
            return None, None

        try:
            preview_data = preview_data.decode(encoding)
        except UnicodeDecodeError:
            return None, None

        preview_data = preview_data.replace(',', ', ').replace(';', '; ')
        preview_data = preview_data.strip().split('\n')

        return preview_data, is_preview_full

    def download(self, version_b64):
        uuid = b642uuid(version_b64)
        entry_version = Version.load(g.dbsession, id=uuid)

        data = entry_version.data

        filename = entry_version.ref.filename.encode('utf-8')
        file_ext = entry_version.metadata.get('file_type', '').encode('utf-8')
        if file_ext != '':
            file_ext = '.' + file_ext

        res = Response(
            data,
            headers={'Content-Length': len(data),
                     'Content-Disposition': 'attachment; filename="%s%s"' %
                                            (filename, file_ext)})
        return res


class DiffView(ActionView):

    def index(self, version_b64):
        uuid = b642uuid(version_b64)
        cur_version = Version.load(g.dbsession, id=uuid)
        entry = cur_version.ref
        versions = entry.versions.order_by(Version.updated.desc()).all()
        cur_idx = versions.index(cur_version)
        try:
            prev_version = versions[cur_idx + 1]
        except IndexError:
            # comparing the first version
            raise NotFound

        diff = compare2(prev_version, cur_version)

        self.view.update({'diff_table': diff,
                          'entry': entry,
                          'prev_date': prev_version.updated,
                          'cur_date': cur_version.updated})

        return render_template('diff.html', **self.view)
