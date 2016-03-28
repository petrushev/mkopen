import json

from flask.views import View
from flask.wrappers import Response
from flask.helpers import make_response
from flask.templating import render_template
from flask import current_app, request


class ActionView(View):

    methods = ['GET']

    def __init__(self, action, is_json=False):
        self.action = action
        self.is_json = is_json
        self.view = {}

    def dispatch_request(self):
        action_fc = getattr(self, self.action, None)
        if action_fc is None:
            return Response('Not found', 404)

        result = action_fc()

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
        return render_template('index.html', **self.view)


class SearchView(ActionView):

    def index(self):
        return ''
