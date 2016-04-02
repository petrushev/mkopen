# -*- coding: utf-8 -*-
import json
from os import environ
from itertools import groupby

from flask.views import View
from flask.wrappers import Response
from flask.helpers import make_response
from flask.templating import render_template
from flask import current_app, request, g
from werkzeug.exceptions import BadRequest
from werkzeug.utils import redirect
from sqlalchemy.sql.operators import op
from sqlalchemy.sql.expression import func, and_

from mkopen.db.models import Version, Data
from mkopen.utils import b642uuid, SearchQuery
from operator import itemgetter


GOOGLE_WEBMASTER = environ.get('GOOGLE_WEBMASTER', None)

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
        self.view = {'url_query': q}


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

        self.view.update({'data': data2,
                          'google_webmaster_verifier': GOOGLE_WEBMASTER})

        return render_template('index.html', **self.view)


class SearchView(ActionView):

    def index(self):
        # build filters
        filters = []
        search_info = {}

        if 'search' in request.args:
            query_arg = request.args['search']
            search_info['query'] = query_arg
            for query_part in query_arg.split(' '):
                if query_part == '':
                    continue
                query_filter = func.join_text_array(Data.catalog_id, ' ')\
                                   .ilike('%%%s%%' % query_part)
                filters.append(query_filter)

        if 'catalog' in request.args:
            catalog_filter = request.args['catalog'].split('/')
            search_info['catalog'] = catalog_filter

            filters.append(Data.catalog_id.op('@>')(catalog_filter))

        # redirect if empty search
        if filters == []:
            return redirect('/', 302)

        # query data with the last version as sort key
        sq = g.dbsession.query(Version.data_id, Version.updated,
                               func.max(Version.updated).over(partition_by=Version.data_id)\
                                   .label('max_updated'))\
              .subquery()

        q = g.dbsession.query(Data, sq.c.updated)\
             .join((sq, and_(sq.c.data_id == Data.id,
                             sq.c.updated == sq.c.max_updated)))\

        # set filters
        if len(filters) > 1:
            q = q.filter(*filters)
        elif len(filters) == 1:
            q = q.filter(filters[0])

        q = q.order_by(sq.c.updated.desc(), Data.catalog_id)

        # pagination
        try:
            page = int(request.args['page'])
        except (ValueError, BadRequest):
            page = 1
        offset = (page - 1) * 15

        data = q.offset(offset).limit(16).all()

        final_page = (len(data) != 16)

        # group by catalog
        data.sort(key=catalog_id_getter)

        data2 = [(catalog_id,
                  map(itemgetter0, sorted(catalog_data, key=itemgetter1, reverse=True)))
            for catalog_id, catalog_data in groupby(data, key=catalog_id_getter)]

        self.view.update({'data': data2,
                          'page': page,
                          'final_page': final_page,
                          'search': search_info})

        return render_template('index.html', **self.view)


class EntryView(ActionView):

    def index(self, data_b64):
        uuid = b642uuid(data_b64)
        entry = Data.load(g.dbsession, id=uuid)

        versions = entry.versions.all()

        self.view.update({'entry': entry, 'versions': versions})

        return render_template('entry.html', **self.view)

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
