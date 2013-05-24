import json
import csv
from zope.component import queryMultiAdapter
from Products.Five.browser import BrowserView

class ExportCSV(BrowserView):
    """ Export to CSV
    """

    def datapoints(self, writer, chart_data):
        """ Export single dimension series to CSV
        """
        for series in chart_data:
            for point in series['data']:
                encoded = {}
                encoded['series'] = series['name']
                for key in ['code', 'y']:
                    encoded[key] = unicode(point[key]).encode('utf-8')
                writer.writerow(encoded)


    def datapoints_xy(self, points):
        """
        """
        return "Not implemented error"

    def export(self):
        """ Export to csv
        """

        self.request.response.setHeader(
            'Content-Type', 'application/csv')
        self.request.response.setHeader(
            'Content-Disposition',
            'attachment; filename="%s.csv"' % self.context.getId())

        chart_data = json.loads(self.request.form.pop('chart_data'))

        headers = ['series', 'code', 'y'];
        writer = csv.DictWriter(self.request.response, headers, restval='')
        writer.writeheader()

        formatter = self.datapoints

        formatter(writer, chart_data)

        return self.request.response

class ExportRDF(BrowserView):
    """ Export to RDF
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
            'Content-Type', 'application/rdf+xml')
        self.request.response.setHeader(
            'Content-Disposition',
            'attachment; filename="%s.rdf"' % self.context.getId())

        if not points:
            return ""

        if formatter:
            return formatter(points)

        return ""
