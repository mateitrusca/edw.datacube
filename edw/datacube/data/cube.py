import time
import urllib
import urllib2
import os
import logging
from collections import defaultdict
import jinja2
import sparql

SPARQL_DEBUG = bool(os.environ.get('SPARQL_DEBUG') == 'on')

logger = logging.getLogger(__name__)

sparql_env = jinja2.Environment(loader=jinja2.PackageLoader(__name__))
sparql_env.globals['sparql'] = sparql

# DATA_REVISION should be the time of last database modification
DATA_REVISION = str(int(time.time()))


class QueryError(Exception):
    pass


def literal_pairs(pairs):
    return [(sparql.Literal(a), sparql.Literal(b)) for a, b in pairs]


class NotationMap(object):

    def __init__(self, cube):
        self.has_data = False
        self.cube = cube

    def _update(self):
        if self.has_data:
            return
        query = sparql_env.get_template('notations.sparql').render(**{
            'dataset': self.cube.dataset,
        })
        by_notation = defaultdict(dict)
        self.by_uri = {}
        for row in self.cube._execute(query):
            by_notation[row['namespace']][row['notation']] = row
            self.by_uri[row['uri']] = row
        self.by_notation = dict(by_notation)
        self.has_data = True

    def lookup_notation(self, namespace, notation):
        self._update()
        return self.by_notation.get(namespace, {}).get(notation)

    def lookup_uri(self, uri):
        self._update()
        return self.by_uri.get(uri)


class Cube(object):

    def __init__(self, endpoint, dataset):
        self.endpoint = endpoint
        self.dataset = sparql.IRI(dataset)
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
            'dataset': sparql.IRI(dataset),
        })
        return list(self._execute(query))[0]

    def get_dataset_details(self):
        query = sparql_env.get_template('dataset_details.sparql').render(**{
            'dataset': sparql.IRI(self.dataset),
        })
        return list(self._execute(query))

    def get_dimension_labels(self, dimension, value):
        query = sparql_env.get_template('dimension_label.sparql').render(**{
            'dataset': self.dataset,
            'dimension': sparql.Literal(dimension),
            'value': sparql.Literal(value),
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
                'dimension_code': sparql.Literal(dimension),
                'filters': literal_pairs(filters + extra_filters),
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
            'uri_list': [sparql.IRI(uri) for uri in uri_list],
        })
        return {row['uri']: row for row in self._execute(query)}

    def get_dimension_option_metadata(self, dimension, option):
        tmpl = sparql_env.get_template('dimension_option_metadata.sparql')
        query = tmpl.render(**{
            'dataset': self.dataset,
            'dimension_code': sparql.Literal(dimension),
            'option_code': sparql.Literal(option),
        })
        rv = list(self._execute(query))[0]
        return {k: rv[k] for k in rv if rv[k] is not None}

    def get_data(self, columns, filters):
        assert columns[-1] == 'value', "Last column must be 'value'"
        query = sparql_env.get_template('data.sparql').render(**{
            'dataset': self.dataset,
            'columns': [sparql.Literal(c) for c in columns[:-1]],
            'filters': literal_pairs(filters),
            'group_dimensions': self.get_group_dimensions(),
            'notations': self.notations,
        })

        result_columns = []
        for f in columns:
            result_columns.extend([f, '%s-label' %f, '%s-short-label' %f])
        for row in self._execute(query, as_dict=False):
            yield dict(zip(result_columns, row))

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
                'columns': [sparql.Literal(c) for c in columns[:-1]],
                'filters': literal_pairs(filters + list(extra_filters)),
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
        return DATA_REVISION

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
