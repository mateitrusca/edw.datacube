import json
from Products.Five.browser import BrowserView


class DatasetQueryView(BrowserView):
    def __call__(self, endpoint, *args, **kwargs):
        response = self.context.REQUEST.RESPONSE
        response.setHeader('Content-Type', 'application/json')
        return self.do_query(endpoint)

    def do_query(self, endpoint):
        data = [
            {'uri': 'some-dataset-uri-1',
             'title': 'Some dataset 1'},
            {'uri': 'some-dataset-uri-2',
             'title': 'Some dataset 2'},
            {'uri': 'some-dataset-uri-3',
             'title': 'Some dataset 3'},
            {'uri': 'some-dataset-uri-4',
             'title': 'Some dataset 4'},
            {'uri': 'some-dataset-uri-5',
             'title': 'Some dataset 5'}
        ]
        return json.dumps(data)
