import json

from flask.views import View
from flask.wrappers import Response
from flask.helpers import make_response
from flask.templating import render_template
from flask import current_app, request, g

from mkopen.db.models import Version, Data
from mkopen.utils import b642uuid


class ActionView(View):

    methods = ['GET']

    def __init__(self, action, is_json=False):
        self.action = action
        self.is_json = is_json
        self.view = {}

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
        q = g.dbsession.query(Data)\
             .join((Version, Version.data_id==Data.id))\
             .order_by(Version.updated.desc())\
             .limit(10).all()

        self.view['data'] = q

        return render_template('index.html', **self.view)


class SearchView(ActionView):

    def index(self):
        return ''


class DownloadView(ActionView):

    def index(self, version_b64):
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
