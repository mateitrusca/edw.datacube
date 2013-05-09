import time
import urllib
import urllib2
import os
import logging
from collections import defaultdict
import threading
import jinja2
import sparql

SPARQL_DEBUG = bool(os.environ.get('SPARQL_DEBUG') == 'on')

logger = logging.getLogger(__name__)

sparql_env = jinja2.Environment(loader=jinja2.PackageLoader(__name__))
sparql_env.filters.update({
    'literal_n3': lambda value: sparql.Literal(value).n3(),
    'uri_n3': lambda value: sparql.IRI(value).n3(),
})


class QueryError(Exception):
    pass


class DataCache(object):

    timeout = 300  # 5 minutes

    def __init__(self):
        self.data = {}
        self.lock = threading.Lock()

    def get(self, key, update):
        with self.lock:
            (value, timestamp) = self.data.get(key, (None, 0))
            if time.time() - timestamp > self.timeout:
                value = update()
                self.data[key] = (value, time.time())
        return value


data_cache = DataCache()


class NotationMap(object):

    def __init__(self, cube):
        self.cube = cube

    def update(self):
        query = sparql_env.get_template('notations.sparql').render(**{
            'dataset': self.cube.dataset,
        })
        by_notation = defaultdict(dict)
        by_uri = {}
        for row in self.cube._execute(query):
            by_notation[row['namespace']][row['notation']] = row
            by_uri[row['uri']] = row
        return {
            'by_notation': dict(by_notation),
            'by_uri': by_uri,
        }

    def get(self):
        cache_key = (self.cube.endpoint, self.cube.dataset)
        return data_cache.get(cache_key, self.update)

    def lookup_notation(self, namespace, notation):
        by_notation = self.get()['by_notation']
        return by_notation.get(namespace, {}).get(notation)

    def lookup_uri(self, uri):
        by_uri = self.get()['by_uri']
        return by_uri.get(uri)


class Cube(object):

    def __init__(self, endpoint, dataset):
        self.endpoint = endpoint
        self.dataset = dataset
        self.notations = NotationMap(self)

    def _execute(self, query, as_dict=True):
        if SPARQL_DEBUG:
            logger.info('Running query: \n%s', query)
        try:
            query_object = sparql.Service(self.endpoint).createQuery()
            query_object.method = 'POST'
            res = query_object.query(query)
        except urllib2.HTTPError, e:
            if 400 <= e.code < 600:
                raise QueryError(e.fp.read())
            else:
                raise
        rv = (sparql.unpack_row(r) for r in res)
        if as_dict:
            return (dict(zip(res.variables, r)) for r in rv)
        else:
            return rv

    def get_datasets(self):
        query = sparql_env.get_template('datasets.sparql').render()
        return list(self._execute(query))

    def get_dataset_metadata(self, dataset):
        query = sparql_env.get_template('dataset_metadata.sparql').render(**{
            'dataset': dataset,
        })
        return list(self._execute(query))[0]

    def get_dataset_details(self):
        query = sparql_env.get_template('dataset_details.sparql').render(**{
            'dataset': self.dataset,
        })
        return list(self._execute(query))

    def get_dimension_labels(self, dimension, value):
        query = sparql_env.get_template('dimension_label.sparql').render(**{
            'dataset': self.dataset,
            'dimension': dimension,
            'value': value,
            'group_dimensions': self.get_group_dimensions(),
            'notations': self.notations,
        })
        return list(self._execute(query))

    def get_dimensions(self, flat=False):
        query = sparql_env.get_template('dimensions.sparql').render(**{
            'dataset': self.dataset,
        })
        result = self._execute(query)
        if flat:
            return list(result)
        else:
            rv = defaultdict(list)
            for row in result:
                rv[row['type_label']].append({
                    'label': row['label'],
                    'notation': row['notation'],
                    'comment': row['comment'],
                })
            return dict(rv)

    def get_group_dimensions(self):
        query = sparql_env.get_template('group_dimensions.sparql').render(**{
            'dataset': self.dataset,
        })
        return sorted([r['group_notation'] for r in self._execute(query)])

    def get_dimension_options(self, dimension, filters=[]):
        # fake an n-dimensional query, with a single dimension, that has no
        # specific filters
        n_filters = [[]]
        return self.get_dimension_options_n(dimension, filters, n_filters)

    def get_dimension_options_xy(self, dimension,
                                 filters, x_filters, y_filters):
        n_filters = [x_filters, y_filters]
        return self.get_dimension_options_n(dimension, filters, n_filters)

    def get_other_labels(self, uri):
        if '#' in uri:
            uri_label = uri.split('#')[-1]
        else:
            uri_label = uri.split('/')[-1]
        return { "group_notation": None,
                 "label": uri_label,
                 "notation": uri_label,
                 "short_label": None,
                 "uri": uri,
                 "order": None }

    def get_dimension_options_xyz(self, dimension,
                                  filters, x_filters, y_filters, z_filters):
        n_filters = [x_filters, y_filters, z_filters]
        return self.get_dimension_options_n(dimension, filters, n_filters)

    def get_dimension_options_n(self, dimension, filters, n_filters):
        uris = None
        for extra_filters in n_filters:
            query = sparql_env.get_template('dimension_options.sparql').render(**{
                'dataset': self.dataset,
                'dimension_code': dimension,
                'filters': filters + extra_filters,
                'group_dimensions': self.get_group_dimensions(),
                'notations': self.notations,
            })
            result = set([item['uri'] for item in self._execute(query)])
            if uris is None:
                uris = result
            else:
                uris = uris & result
        labels = self.get_labels(uris)
        rv = [labels.get(uri, self.get_other_labels(uri)) for uri in uris]
        rv.sort(key=lambda item: int(item.pop('order') or '0'))
        return rv

    def get_labels(self, uri_list):
        if len(uri_list) < 1:
            return {}
        tmpl = sparql_env.get_template('labels.sparql')
        query = tmpl.render(**{
            'uri_list': uri_list,
        })
        return {row['uri']: row for row in self._execute(query)}

    def get_dimension_option_metadata(self, dimension, option):
        tmpl = sparql_env.get_template('dimension_option_metadata.sparql')
        query = tmpl.render(**{
            'dataset': self.dataset,
            'dimension_code': dimension,
            'option_code': option,
        })
        rv = list(self._execute(query))[0]
        return {k: rv[k] for k in rv if rv[k] is not None}

    def get_data(self, columns, filters):
        assert columns[-1] == 'value', "Last column must be 'value'"
        query = sparql_env.get_template('data.sparql').render(**{
            'dataset': self.dataset,
            'columns': columns[:-1],
            'filters': filters,
            'group_dimensions': self.get_group_dimensions(),
            'notations': self.notations,
        })

        result_columns = []
        for f in columns:
            result_columns.extend([f, '%s-label' %f, '%s-short-label' %f])
        for row in self._execute(query, as_dict=False):
            yield dict(zip(result_columns, row))

    def get_observations(self, filters):
        def mapper(item):
            if not item['type_label'] in ['measure', 'dimension group']:
                is_attr = True if item['type_label'] == 'attribute' else False
                return { "uri": item['dimension'],
                         "optional": is_attr,
                         "notation": item['notation'],
                         "name": item['notation']}
        columns = filter(lambda item: True if item else False,
                         map(mapper, self.get_dimensions(flat=True)))
        query = sparql_env.get_template('data_and_attributes.sparql').render(**{
            'dataset': self.dataset,
            'columns': columns,
            'filters': filters,
            'group_dimensions': self.get_group_dimensions(),
            'notations': self.notations,
        })
        result = list(self._execute(query, as_dict=False))
        def reducer(memo, item):
            return memo.union(set([uri for uri in item[:-1] if uri]))
        uris = reduce(reducer, result, set())
        labels = self.get_labels(uris)

        result_columns = []
        for f in columns:
            n = f['notation']
            result_columns.extend([n, '%s-label' %n, '%s-short-label' %n])

        for row in result:
            result_row = []
            value = row.pop(-1)
            for item in row:
                result_row.extend(
                    [labels.get(item, {}).get('notation', None),
                    labels.get(item, {}).get('label', None),
                    labels.get(item, {}).get('short_label', None)]
                )
            result_columns.append('value')
            result_row.append(value)
            yield dict(zip(result_columns, result_row))

    def get_data_xy(self, columns, xy_columns, filters, x_filters, y_filters):
        n_filters = [x_filters, y_filters]
        return self.get_data_n(columns + xy_columns, filters, n_filters)

    def get_data_xyz(self, columns, xyz_columns, filters, x_filters, y_filters,
                     z_filters):
        n_filters = [x_filters, y_filters, z_filters]
        return self.get_data_n(columns + xyz_columns, filters, n_filters)

    def get_data_n(self, columns, filters, n_filters):
        assert columns[-1] == 'value'

        raw_result = []
        idx = 0
        for extra_filters in n_filters:
            query = sparql_env.get_template('data.sparql').render(**{
                'dataset': self.dataset,
                'columns': columns[:-1],
                'filters': filters + list(extra_filters),
                'group_dimensions': self.get_group_dimensions(),
                'notations': self.notations,
            })
            container = {}
            for row in self._execute(query, as_dict=False):
                container[row[0]] = zip(columns, [row[0], row[-1]])
            raw_result.append(container)
        def find_common(memo, item):
            inter_common = set(memo).intersection(set(item.keys()))
            return inter_common
        common = reduce(find_common, raw_result, raw_result[0].keys())

        dimensions = ['x', 'y', 'z']
        for item in common:
            out = dict([raw_result[0][item][0]])
            out['value'] = {dimensions[n]: raw_result[n][item][-1][-1]
                            for n in range(len(raw_result))}
            yield dict(out)

    def get_revision(self):
        query = sparql_env.get_template('last_modified.sparql').render()
        return unicode(next(self._execute(query))['modified'])

    def dump(self, data_format=''):
        query = sparql_env.get_template('dump.sparql').render(**{
            'dataset': self.dataset,
        })
        if data_format:
            params = urllib.urlencode({
                'query': query,
                'format': data_format,
            })
            result = urllib2.urlopen(self.endpoint, data=params)
            return result.read()
        return self._execute(query)
