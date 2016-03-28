# from os.path import dirname
# from os.path import join as path_join
from os import environ
import json
from urlparse import urlparse

from flask import Flask, g, request
from flask.templating import render_template
from flask.helpers import url_for
from werkzeug.urls import url_quote, url_quote_plus
from werkzeug.datastructures import ImmutableMultiDict

from mkopen.views import IndexView, SearchView
from mkopen.db.mappers import sessionmaker


NAIVE_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT = '%Y-%m-%d'

STATIC_URL_PATH = environ.get('MKOPEN_STATIC_URL_PATH', '/static')

routes = [
    ('/', IndexView.as_view('home', 'index')),
    ('/search', SearchView.as_view('search', 'index')),
]

def is_json(request):
    """
    Indicates if this request is JSON or not.  By default a request
    is considered to include JSON data if the mimetype is
    ``application/json`` or ``application/*+json``.

    .. versionadded:: 0.11
    """
    # TODO Should be removed once Flask upgrades to 0.11
    mt = request.mimetype
    if mt == 'application/json':
        return True
    if mt.startswith('application/') and mt.endswith('+json'):
        return True
    return False

def error_404(e):
    return render_template('error/404.html'), 404

def create_app():
    app_ = Flask(__name__, static_url_path=STATIC_URL_PATH)

    app_.jinja_env.globals.update(cdn=STATIC_URL_PATH,
                                 url_for=url_for,
                                 url_quote=url_quote,
                                 url_quote_plus=url_quote_plus,
                                 DATE_FORMAT=DATE_FORMAT,
                                 NAIVE_DATETIME_FORMAT=NAIVE_DATETIME_FORMAT)
    app_.jinja_env.filters.update(json=json.dumps,
                                 domain=lambda url: urlparse(url).netloc)

    for path, view in routes:
        app_.add_url_rule(path, view_func=view)

    app_.errorhandler(404)(error_404)

    app_.Session = sessionmaker(
        {'url': 'postgres://%s/%s' % (environ['OPENSHIFT_POSTGRESQL_DB_URL'], environ['PGDATABASE']),
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
