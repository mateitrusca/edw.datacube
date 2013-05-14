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
        """ Datapoints for country profile chart
        """
        subtype = self.request.form.pop('subtype', 'table')
        if subtype == 'table':
            return self.datapoints_cpt()
        else:
            return self.datapoints_cpc()

    @eeacache(cacheKey, dependencies=['edw.datacube'])
    def datapoints_cpc(self):
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
                    #'rank': {'value': 0, 'ref-area': countryName}
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

            ## Update rank only for EU27 countries
            #if countryName not in eu:
                #continue

            #if not mapping[key]['rank']['value']:
                #mapping[key]['rank']['value'] = 1
            #if point['value'] > countryValue:
                #mapping[key]['rank']['value'] += 1

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
            #rank = mapping[key]['rank']['value']

            point['original'] = val
            point['eu'] = medVal
            #point['rank'] = rank

            if val <= medVal:
                point['value'] = (val - minVal) / (medVal - minVal)
            else:
                point['value'] = 1 + (val - medVal) / (maxVal - medVal)
            rows.append(point)

        return self.jsonify({'datapoints': rows})

    @eeacache(cacheKey, dependencies=['edw.datacube'])
    def datapoints_cpt(self):
        """ Datapoints for country profile table

        return_json = {
          'datapoints' {
            'latest': 2012,
            'has-rank': true,
            'ref-area': {
              'label': 'Romania',
              'short-label': null,
              'notation': 'RO'
            },
           'table': {
             'indicator-1,breakdown-1,unit-measure-1': {
               'name': ('Indicator-1-short-label by '
                        'breakdown-1-label in '
                        'unit-measure-1-label'),
               'rank': 15,
               'eu': 0.67,
               '2012': 0.55,
               '2011': 0.46,
               '2010': 0.33,
               '2009': 0.09,
               '2008': 0.01
             },
             'indicator-2,breakdown-2,unit-measure-2': {
               'name': ('Indicator-2-short-label by '
                        'breakdown-2-label in '
                        'unit-measure-2-label'),
               'rank': 2,
               'eu': 0.78,
               '2012': 0.15,
               '2011': 0.46,
               '2010': 0.89
             }
           }
          }
        }
        """
        # Get datapoints
        datapoints = json.loads(self.datapoints())
        countryName = self.request.form.pop('ref-area', '')
        latestYear = 2000
        mapping = {
            'latest': latestYear,
            'has-rank': False,
            'ref-area': {
                'notation': countryName,
                'label': countryName,
                'short-label': None
            },
            'table': {}
        }
        table = mapping['table']

        for point in datapoints['datapoints']:
            # Selected country
            mapping['ref-area'].update(point['ref-area'])

            # Indicator unique identifier
            key = u','.join((
                point['indicator']['notation'],
                point['breakdown']['notation'],
                point['unit-measure']['notation']
            ))

            try:
                point['value'] = float(point['value'])
            except Exception, err:
                logger.exception(err)
                continue

            table.setdefault(key, {})
            if not table[key].get('name', ''):
                name = point['indicator']['short-label']
                if point['breakdown']['label']:
                    name += u' by ' + point['breakdown']['label']
                if point['unit-measure']['label']:
                    name += u' in ' + point['unit-measure']['label']
                table[key]['name'] = name

            year = point['time-period']['notation']
            try:
                year = int(year)
            except Exception, err:
                logger.exception(err)
                continue

            latestYear = max(latestYear, year)
            mapping['latest'] = latestYear
            table[key][year] = point['value']
            table[key].setdefault('rank', 0)


        # Get EU countries
        view = queryMultiAdapter((self.context, self.request),
                                 name=u'european-union.json')
        eu = view.eu if view else {}

        # Get all datapoints
        all_datapoints = json.loads(self.datapoints())

        # Compute rank amoung EU27 countries
        for point in all_datapoints['datapoints']:
            key = u','.join((
                point['indicator']['notation'],
                point['breakdown']['notation'],
                point['unit-measure']['notation']
            ))

            year = point['time-period']['notation']
            try:
                year = int(year)
            except Exception, err:
                logger.exception(err)
                continue

            # Skip old values
            if year != latestYear:
                continue

            try:
                point['value'] = float(point['value'])
            except Exception, err:
                logger.exception(err)
                continue

            if point['ref-area']['notation'] == 'EU27':
                if table.get(key):
                    table[key]['eu'] = point['value']

            # Update rank only for EU27 countries
            if countryName not in eu:
                continue

            # Skip non-EU countries from rank computation
            if point['ref-area']['notation'] not in eu:
                continue

            myValue = table.get(key, {}).get(year, None)
            if myValue is not None:
                mapping['has-rank'] = True
                if not table[key].get('rank'):
                    table[key]['rank'] = 1
                if point['value'] > myValue:
                    table[key]['rank'] += 1

        return self.jsonify({'datapoints': mapping})

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
