""" Query
"""
import csv
import json
import logging
from zope.component import queryMultiAdapter
from Products.Five.browser import BrowserView
from eea.cache import cache as eeacache

logger = logging.getLogger('edw.datacube')

def jsonify(request, data, cache=True):
    header = request.RESPONSE.setHeader
    header("Content-Type", "application/json")
    if cache:
        header("Expires", "Sun, 17-Jan-2038 19:14:07 GMT")
    return json.dumps(data, indent=2, sort_keys=True)

def cacheKey(method, self, *args, **kwargs):
    """ Generate unique cache id
    """
    return (self.context.absolute_url(1), dict(self.request.form))

class AjaxDataView(BrowserView):

    def __init__(self, context, request):
        super(AjaxDataView, self).__init__(context, request)
        self.endpoint = self.request.get('endpoint', '')
        self.cube = context.get_cube(self.endpoint)

    def jsonify(self, *args, **kwargs):
        return jsonify(self.request, *args, **kwargs)

    def datasets(self):
        return self.jsonify({'datasets': self.cube.get_datasets()},
                            cache=False)

    def dataset_metadata(self):
        dataset = self.request.form['dataset']
        return self.jsonify(self.cube.get_dataset_metadata(dataset))

    def dataset_details(self):
        return self.jsonify(self.cube.get_dataset_details())

    def get_dimensions(self):
        flat = bool(self.request.form.get('flat'))
        dimensions = self.cube.get_dimensions(flat=flat)
        return self.jsonify(dimensions)

    @eeacache(cacheKey, dependencies=['edw.datacube'])
    def dimension_labels(self):
        form = dict(self.request.form)
        dimension = form.pop('dimension')
        value = form.pop('value')
        [labels] = self.cube.get_dimension_labels(dimension, value)
        return self.jsonify(labels)

    @eeacache(cacheKey, dependencies=['edw.datacube'])
    def dimension_options(self):
        form = dict(self.request.form)
        form.pop('rev', None)
        dimension = form.pop('dimension')
        filters = sorted(form.items())
        options = self.cube.get_dimension_options(dimension, filters)
        return self.jsonify({'options': options})

    @eeacache(cacheKey, dependencies=['edw.datacube'])
    def dimension_options_xy(self):
        form = dict(self.request.form)
        form.pop('rev', None)
        dimension = form.pop('dimension')
        (filters, x_filters, y_filters) = ([], [], [])
        for k, v in sorted(form.items()):
            if k.startswith('x-'):
                x_filters.append((k[2:], v))
            elif k.startswith('y-'):
                y_filters.append((k[2:], v))
            else:
                filters.append((k, v))
        options = self.cube.get_dimension_options_xy(dimension, filters,
                                                     x_filters, y_filters)
        return self.jsonify({'options': options})

    @eeacache(cacheKey, dependencies=['edw.datacube'])
    def dimension_options_xyz(self):
        form = dict(self.request.form)
        form.pop('rev', None)
        dimension = form.pop('dimension')
        (filters, x_filters, y_filters, z_filters) = ([], [], [], [])
        for k, v in sorted(form.items()):
            if k.startswith('x-'):
                x_filters.append((k[2:], v))
            elif k.startswith('y-'):
                y_filters.append((k[2:], v))
            elif k.startswith('z-'):
                z_filters.append((k[2:], v))
            else:
                filters.append((k, v))
        options = self.cube.get_dimension_options_xyz(dimension, filters,
                                                      x_filters, y_filters,
                                                      z_filters)
        return self.jsonify({'options': options})

    @eeacache(cacheKey, dependencies=['edw.datacube'])
    def dimension_options_cp(self):
        subtype = self.request.form.pop('subtype', 'table')
        options = self.dimension_options()

        if self.request.form.get('dimension', '') != 'ref-area':
            return options

        if subtype == u'table':
            return options

        # Get EU countries
        view = queryMultiAdapter((self.context, self.request),
                                 name=u'european-union.json')
        eu = view.eu if view else {}

        options = json.loads(options)

        rows = []
        for option in options.get('options', []):
            if option.get('notation', '') not in eu:
                continue
            rows.append(option)
        return self.jsonify({'options': rows})


    def dimension_value_metadata(self):
        dimension = self.request.form['dimension']
        value = self.request.form['value']
        res = self.cube.get_dimension_option_metadata(dimension, value)
        return self.jsonify(res)

    def country_value(self, uid, datapoints):
        """ Get value for given uid
        """
        for point in datapoints:
            key = (
                point['indicator']['notation'],
                point['breakdown']['notation'],
                point['unit-measure']['notation']
            )
            if uid == key:
                res = point['value']
                try:
                    res = float(res)
                except Exception, err:
                    logger.exception(err)
                    return 0
                else:
                    return res
        return 0

    def blacklisted(self, point, blacklist):
        """ Check to see if point is blacklisted
        """
        for black in blacklist:
            match = True
            for key, value in black.items():
                if point.get(key, {}).get('notation', u'') != value:
                    match = False
                    break
            if match:
                return True
        return False

    @eeacache(cacheKey, dependencies=['edw.datacube'])
    def datapoints(self):
        form = dict(self.request.form)
        form.pop('rev', None)
        columns = form.pop('columns', form.pop('fields', '')).split(',')
        filters = sorted(form.items())
        rows = list(self.cube.get_observations(filters=filters))
        return self.jsonify({'datapoints': rows})

    @eeacache(cacheKey, dependencies=['edw.datacube'])
    def datapoints_cp(self):
        """ Datapoints for country profile
        """
        # Get datapoints
        datapoints = json.loads(self.datapoints())

        # Get EU countries
        view = queryMultiAdapter((self.context, self.request),
                                 name=u'european-union.json')
        eu = view.eu if view else {}

        # Get blacklisted items
        view = queryMultiAdapter((self.context, self.request),
                                 name=u'blacklist.json')
        blacklist = view.blacklist if view else []

        # Get all datapoints
        countryName = self.request.form.pop('ref-area', '')
        all_datapoints = json.loads(self.datapoints())

        # Compute new values
        mapping = {}
        for point in all_datapoints['datapoints']:
            if self.blacklisted(point, blacklist):
                continue

            key = (
                point['indicator']['notation'],
                point['breakdown']['notation'],
                point['unit-measure']['notation']
            )

            try:
                point['value'] = float(point['value'])
            except Exception, err:
                logger.exception(err)
                continue

            countryValue = self.country_value(key, datapoints['datapoints'])
            if not mapping.get(key):
                mapping[key] = {
                    'min': {'value': countryValue, 'ref-area': countryName},
                    'max': {'value': countryValue, 'ref-area': countryName},
                    'med': {'value': countryValue, 'ref-area': countryName},
                    'rank': {'value': 0, 'ref-area': countryName}
            }

            # Update med
            if point['ref-area']['notation'] == 'EU27':
                mapping[key]['med']['value'] = point['value']
                mapping[key]['med']['ref-area'] = point['ref-area']['notation']

            # Update min / max only for EU27 countries
            if point['ref-area']['notation'] not in eu:
                continue

            # Update min
            oldValue = mapping[key]['min']['value']
            newValue = min(point['value'], oldValue);
            if newValue != oldValue:
                mapping[key]['min']['value'] = newValue
                mapping[key]['min']['ref-area'] = point['ref-area']['notation']

            # Update max
            oldValue = mapping[key]['max']['value']
            newValue = max(point['value'], oldValue)
            if newValue != oldValue:
                mapping[key]['max']['value'] = newValue
                mapping[key]['max']['ref-area'] = point['ref-area']['notation'];

            # Update rank onlu for EU27 countries
            if countryName not in eu:
                continue

            if not mapping[key]['rank']['value']:
                mapping[key]['rank']['value'] = 1
            if point['value'] > countryValue:
                mapping[key]['rank']['value'] += 1

        # Update points
        rows = []
        for point in datapoints['datapoints']:
            if self.blacklisted(point, blacklist):
                continue

            key =  (
                point['indicator']['notation'],
                point['breakdown']['notation'],
                point['unit-measure']['notation']
            )

            try:
                point['value'] = float(point['value'])
            except Exception, err:
                logger.exception(err)
                continue

            val = point['value']
            minVal = mapping[key]['min']['value']
            maxVal = mapping[key]['max']['value']
            medVal = mapping[key]['med']['value']
            rank = mapping[key]['rank']['value']

            point['original'] = val
            point['eu'] = medVal
            point['rank'] = rank

            if val <= medVal:
                point['value'] = (val - minVal) / (medVal - minVal)
            else:
                point['value'] = 1 + (val - medVal) / (maxVal - medVal)
            rows.append(point)

        return self.jsonify({'datapoints': rows})

    @eeacache(cacheKey, dependencies=['edw.datacube'])
    def datapoints_xy(self):
        form = dict(self.request.form)
        form.pop('rev', None)
        join_by = form.pop('join_by')
        (filters, x_filters, y_filters) = ([], [], [])
        for k, v in sorted(form.items()):
            if k.startswith('x-'):
                x_filters.append((k[2:], v))
            elif k.startswith('y-'):
                y_filters.append((k[2:], v))
            else:
                filters.append((k, v))
        rows = list(self.cube.get_data_xy(join_by=join_by,
                                          filters=filters,
                                          x_filters=x_filters,
                                          y_filters=y_filters))
        return self.jsonify({'datapoints': rows})

    @eeacache(cacheKey, dependencies=['edw.datacube'])
    def datapoints_xyz(self):
        form = dict(self.request.form)
        form.pop('rev', None)
        join_by = form.pop('join_by')
        (filters, x_filters, y_filters, z_filters) = ([], [], [], [])
        for k, v in sorted(form.items()):
            if k.startswith('x-'):
                x_filters.append((k[2:], v))
            elif k.startswith('y-'):
                y_filters.append((k[2:], v))
            elif k.startswith('z-'):
                z_filters.append((k[2:], v))
            else:
                filters.append((k, v))
        rows = list(self.cube.get_data_xyz(join_by=join_by,
                                          filters=filters,
                                          x_filters=x_filters,
                                          y_filters=y_filters,
                                          z_filters=z_filters))
        return self.jsonify({'datapoints': rows})

    def dump_csv(self):
        response = self.request.response
        response.setHeader('Content-type', 'text/csv; charset=utf-8')
        filename = self.context.getId() + '.csv'
        response.setHeader('Content-Disposition',
                           'attachment;filename=%s' % filename)
        headers = [
            'indicator',
            'breakdown',
            'unit_measure',
            'time_period',
            'ref_area',
            'value']
        writer = csv.DictWriter(response, headers, restval='')
        writer.writeheader()
        for row in self.cube.dump():
            encoded_row = {}
            for k,v in row.iteritems():
                encoded_row[k] = unicode(v).encode('utf-8')
            writer.writerow(encoded_row)
        return response

    def dump_rdf(self):
        response = self.request.response
        response.setHeader('Content-type', 'application/rdf+xml; charset=utf-8')
        filename = self.context.getId() + '.rdf'
        response.setHeader('Content-Disposition',
                           'attachment;filename=%s' % filename)
        return self.cube.dump(data_format='application/rdf+xml')
