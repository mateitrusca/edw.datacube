import json
from zope.component import queryMultiAdapter
from Products.Five.browser import BrowserView

class ExportCSV(BrowserView):
    """ Export to CSV
    """

    def datapoints(self, points):
        """ xxx
        """
        return "Not implemented error"

    def datapoints_xy(self, points):
        """
        """
        return "Not implemented error"

    def export(self):
        """ Export to csv
        """
        options = self.request.form.get('options', "{}")
        method = self.request.form.get('method', 'datapoints')
        formatter = getattr(self, method, None)

        self.request.form = json.loads(options)
        points = queryMultiAdapter((self.context, self.request), name=method)

        self.request.response.setHeader(
            'Content-Type', 'application/csv')
        self.request.response.setHeader(
            'Content-Disposition',
            'attachment; filename="%s.csv"' % self.context.getId())

        if not points:
            return ""

        if formatter:
            return formatter(points)

        return ""
