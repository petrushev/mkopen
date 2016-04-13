# from os.path import dirname
# from os.path import join as path_join
from os import environ
import json
from urlparse import urlparse

from flask import Flask, g, request
from flask.templating import render_template
from flask.helpers import url_for
from werkzeug.urls import url_quote_plus
from werkzeug.datastructures import ImmutableMultiDict

from mkopen.views import IndexView, SearchView, EntryView, DiffView
from mkopen.utils import uuid2b64, is_json, date_format
from mkopen.db.mappers import sessionmaker


NAIVE_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT = '%Y-%m-%d'

STATIC_URL_PATH = environ.get('MKOPEN_STATIC_URL_PATH', '/static')

routes = [
    ('/', IndexView.as_view('home', 'index')),
    ('/search', SearchView.as_view('search', 'index')),
    ('/search/<string:query>', SearchView.as_view('search_query', 'search')),
    ('/catalog/<path:catalog_id>', SearchView.as_view('catalog', 'catalog')),
    ('/download/<string:version_b64>', EntryView.as_view('download', 'download')),
    ('/entry/<string:data_b64>', EntryView.as_view('entry', 'index')),
    ('/diff/<string:version_b64>', DiffView.as_view('diff', 'index')),
    ('/robots.txt', IndexView.as_view('robots', 'robots')),
]


def error_404(e):
    return render_template('error/404.html'), 404

def create_app():
    app_ = Flask(__name__, static_url_path=STATIC_URL_PATH)

    app_.jinja_env.globals.update(cdn=STATIC_URL_PATH,
                                  url_for=url_for,
                                  url_quote=url_quote_plus,
                                  DATE_FORMAT=DATE_FORMAT,
                                  NAIVE_DATETIME_FORMAT=NAIVE_DATETIME_FORMAT)
    app_.jinja_env.filters.update(date_format=date_format)
    app_.jinja_env.filters.update(json=json.dumps,
                                  domain=lambda url: urlparse(url).netloc,
                                  uuid2b64=uuid2b64)

    for path, view in routes:
        app_.add_url_rule(path, view_func=view)

    app_.errorhandler(404)(error_404)

    app_.Session = sessionmaker(
        {'url': '%s/%s' % (environ['OPENSHIFT_POSTGRESQL_DB_URL'], environ['PGDATABASE']),
         'echo': False})

    @app_.before_request
    def before_request_callback():
        # create db session
        g.dbsession = app_.Session()

        # check if the post data is via json
        if is_json(request):
            request.form = ImmutableMultiDict(request.get_json())

    @app_.after_request
    def after_request_callback(response):
        # close db session
        g.dbsession.close()
        return response

    return app_
