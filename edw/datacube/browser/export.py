import json
import csv
from zope.component import queryMultiAdapter
from Products.Five.browser import BrowserView

class ExportCSV(BrowserView):
    """ Export to CSV
    """

    def datapoints(self, response, chart_data):
        """ Export single dimension series to CSV
        """
        try:
            if len(chart_data) < 1:
                return ""
        except:
            return ""

        headers = ['series', 'code', 'y']

        keys = chart_data[0].get('data', [{}])[0].keys()

        writer = csv.DictWriter(response, headers, restval='')
        writer.writeheader()

        for series in chart_data:
            for point in series['data']:
                encoded = {}
                encoded['series'] = series.get('name', '-')
                for key in headers[1:]:
                    encoded[key] = unicode(point.get(key, '-')).encode('utf-8')
                writer.writerow(encoded)


    def datapoints_n(self, response, chart_data):
        """ Export multiple dimension series to CSV
        """
        try:
            if len(chart_data) < 1:
                return ""
        except:
            return ""

        coords = set(['x', 'y', 'z'])
        keys = set(chart_data[0][0].get('data', [{}])[0].keys())

        headers = ['series', 'name', 'x', 'y', 'z']

        if keys.intersection(coords) != coords:
            headers = ['series', 'name', 'x', 'y']

        writer = csv.DictWriter(response, headers, restval='')
        writer.writeheader()

        for series in chart_data:
            for point in series:
                encoded = {}
                encoded['series'] = point['name']
                for data in point['data']:
                    for key in headers[1:]:
                        encoded[key] = unicode(data[key]).encode('utf-8')
                    writer.writerow(encoded)


    def datapoints_profile(self, response, chart_data):
        headers = ['name', 'eu', 'original']
        extra_headers = ['period']

        writer = csv.DictWriter(response, extra_headers + headers, restval='')
        writer.writeheader()

        for series in chart_data:
            for point in series['data']:
                encoded = {}
                for key in headers:
                    encoded[key] = unicode(point[key]).encode('utf-8')
                period = point['attributes']['time-period']['notation']
                encoded['period'] = unicode(period).encode('utf-8')
                writer.writerow(encoded)


    def datapoints_profile_table(self, response, chart_data):
        for series in chart_data:
            encoded = {}
            latest = series['data']['latest']
            years = ['%s' % (latest-3), '%s' % (latest-2), '%s' % (latest-1), '%s' % (latest)]

            headers = (['country', 'indicator', 'breakdown', 'unit'] + years +
                       ['EU27 value %s' %latest, 'rank'])
            writer = csv.DictWriter(response, headers, restval='')
            writer.writeheader()

            encoded['country'] = series['data']['ref-area']['label']
            for ind in series['data']['table'].values():
                encoded['indicator'] = unicode(ind['indicator']).encode('utf-8')
                encoded['breakdown'] = unicode(ind['breakdown']).encode('utf-8')
                encoded['unit'] = unicode(ind['unit-measure']).encode('utf-8')
                for year in years:
                    encoded[year] = unicode(ind.get(year, '-')).encode('utf-8')
                #encoded['%s' %latest] = unicode(ind.get('%s' %latest, '-')).encode('utf-8')
                encoded['EU27 value %s' %latest] = unicode(
                        ind.get('eu', '-')).encode('utf-8')
                rank = ind.get('rank', '-')
                if rank == 0:
                    rank = '-'
                encoded['rank'] = unicode(rank).encode('utf-8')
                writer.writerow(encoded)


    def export(self):
        """ Export to csv
        """

        self.request.response.setHeader(
            'Content-Type', 'application/csv')
        self.request.response.setHeader(
            'Content-Disposition',
            'attachment; filename="%s.csv"' % self.context.getId())

        chart_data = json.loads(self.request.form.pop('chart_data'))

        chart_type = self.request.form.pop('chart_type')

        formatters = {
            'scatter': self.datapoints_n,
            'bubbles': self.datapoints_n,
            'country_profile_bar': self.datapoints_profile,
            'country_profile_table': self.datapoints_profile_table
        }

        formatter = formatters.get(chart_type, self.datapoints)

        formatter(self.request.response, chart_data)

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
