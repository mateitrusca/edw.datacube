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

    def __init__(self):
        self.data = {}
        self.timestamp = None
        self.lock = threading.Lock()

    def ping(self, timestamp):
        with self.lock:
            if timestamp != self.timestamp:
                self.data.clear()
                self.timestamp = timestamp

    def get(self, key, update):
        with self.lock:
            if key not in self.data:
                self.data[key] = update()
            return self.data[key]


data_cache = DataCache()


class NotationMap(object):

    NAMESPACES = [
        ('breakdown', 'http://semantic.digital-agenda-data.eu/'
                      'codelist/breakdown/'),
        ('indicator', 'http://semantic.digital-agenda-data.eu/'
                      'codelist/indicator/'),
        ('breakdown-group', 'http://semantic.digital-agenda-data.eu/'
                            'codelist/breakdown-group/'),
        ('time-period', 'http://reference.data.gov.uk/id/gregorian-year/'),
        ('flag', 'http://eurostat.linked-statistics.org/dic/flags#'),
        ('indicator-group', 'http://semantic.digital-agenda-data.eu/'
                            'codelist/indicator-group/'),
        ('unit-measure', 'http://semantic.digital-agenda-data.eu/'
                         'codelist/unit-measure/'),
        ('ref-area', 'http://eurostat.linked-statistics.org/dic/geo#'),
    ]

    def __init__(self, cube):
        self.cube = cube

    def update(self):
        t0 = time.time()
        logger.info('loading notation cache')
        query = sparql_env.get_template('notations.sparql').render(**{
            'dataset': self.cube.dataset,
        })
        by_notation = defaultdict(dict)
        by_uri = {}
        for row in self.cube._execute(query):
            by_notation[row['namespace']][row['notation']] = row
            by_uri[row['uri']] = row
        logger.info('notation cache loaded, %.2f seconds', time.time() - t0)
        return {
            'by_notation': dict(by_notation),
            'by_uri': by_uri,
        }

    def get(self):
        cache_key = (self.cube.endpoint, self.cube.dataset)
        return data_cache.get(cache_key, self.update)

    def lookup_notation(self, namespace, notation):
        by_notation = self.get()['by_notation']
        ns = by_notation.get(namespace)
        if ns is None:
            raise RuntimeError("Unknown namespace %r", namespace)
        rv = ns.get(notation)
        if rv is None:
            logger.warn('lookup failure %r', (namespace, notation))
        return rv

    def lookup_uri(self, uri):
        by_uri = self.get()['by_uri']
        return by_uri.get(uri)

    def touch_uri(self, uri):
        data = self.get()
        if uri not in data['by_uri']:
            for namespace, prefix in self.NAMESPACES:
                if uri.startswith(prefix):
                    notation = uri[len(prefix):]
                    logger.info('patching missing notation %r',
                                (namespace, notation))
                    row = {'uri': uri,
                           'namespace': namespace,
                           'notation': notation}
                    data['by_uri'][uri] = row
                    data['by_notation'][namespace][notation] = row
                    break
            else:
                logger.warn('new unknown uri %r', uri)


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
        res = list(self._execute(query))
        res_by_uri = {row['indicator']: row for row in res}
        meta_list = self.get_dimension_option_metadata_list(list(res_by_uri))
        for meta in meta_list:
            uri = meta.pop('uri')
            meta['altlabel'] = meta.pop('short_label', None)
            meta['sourcelabel'] = meta.pop('source_label', None)
            meta['sourcelink'] = meta.pop('source_url', None)
            meta['sourcenotes'] = meta.pop('source_notes', None)
            meta['notes'] = meta.pop('note', None)
            meta['longlabel'] = meta.pop('label', None)
            res_by_uri[uri].update(meta)
        return res

    def get_dimension_labels(self, dimension, value):
        query = sparql_env.get_template('dimension_label.sparql').render(**{
            'dataset': self.dataset,
            'dimension': dimension,
            'value': value,
            'group_dimensions': self.get_group_dimensions(),
            'notations': self.notations,
        })
        rv = list(self._execute(query))
        if not rv:
            rv = [{'label': value, 'short_label': None}]
        return rv

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

    def load_group_dimensions(self):
        query = sparql_env.get_template('group_dimensions.sparql').render(**{
            'dataset': self.dataset,
        })
        return sorted([r['group_notation'] for r in self._execute(query)])

    def get_group_dimensions(self):
        cache_key = (self.endpoint, self.dataset, 'get_group_dimensions')
        return data_cache.get(cache_key, self.load_group_dimensions)

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
        for uri in uri_list:
            self.notations.touch_uri(uri)
        query = tmpl.render(**{
            'uri_list': uri_list,
        })
        return {row['uri']: row for row in self._execute(query)}

    def get_dimension_option_metadata_list(self, uri_list):
        tmpl = sparql_env.get_template('dimension_option_metadata.sparql')
        query = tmpl.render(**{
            'dataset': self.dataset,
            'uri_list': uri_list,
        })
        res = list(self._execute(query))
        return [{k: row[k] for k in row if row[k] is not None} for row in res]

    def get_dimension_option_metadata(self, dimension, option):
        uri = self.notations.lookup_notation(dimension, option)['uri']
        res = self.get_dimension_option_metadata_list([uri])
        if res:
            return res[0]
        else:
            return {}

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

    def get_columns(self):
        def mapper(item):
            if not item['type_label'] in ['measure', 'dimension group']:
                is_attr = True if item['type_label'] == 'attribute' else False
                return { "uri": item['dimension'],
                         "optional": is_attr,
                         "notation": item['notation'],
                         "name": item['notation']}
        columns = filter(lambda item: True if item else False,
                         map(mapper, self.get_dimensions(flat=True)))
        return columns

    def get_observations(self, filters):
        columns = self.get_columns()
        query = sparql_env.get_template('data_and_attributes.sparql').render(**{
            'dataset': self.dataset,
            'columns': columns,
            'filters': filters,
            'group_dimensions': self.get_group_dimensions(),
            'notations': self.notations,
        })
        result = list(self._execute(query, as_dict=False))
        def reducer(memo, item):
            def uri_filter(uri):
                if uri:
                    return True if uri.startswith('http://') else False
            return memo.union(set(filter(uri_filter, item[:-1])))
        uris = reduce(reducer, result, set())
        labels = self.get_labels(uris)

        result_columns = [item['notation'] for item in columns] + ['value']

        for row in result:
            result_row = []
            value = row.pop(-1)
            for item in row:
                if item not in uris:
                    result_row.append(item)
                else:
                    result_row.append(
                        {'notation': labels.get(item, {}).get('notation', None),
                         'label': labels.get(item, {}).get('label', None),
                         'short-label': labels.get(item, {}).get('short_label', None)}
                    )
            result_row.append(value)
            yield dict(zip(result_columns, result_row))

    def get_data_xy(self, join_by, filters, x_filters, y_filters):
        n_filters = [x_filters, y_filters]
        return self.get_data_n(join_by, filters, n_filters)

    def get_data_xyz(self, join_by, filters, x_filters, y_filters,
                     z_filters):
        n_filters = [x_filters, y_filters, z_filters]
        return self.get_data_n(join_by, filters, n_filters)

    def get_data_n(self, join_by, filters, n_filters):
        # GET COLUMNS AND COLUMNS NAMES
        columns = self.get_columns()
        columns_names = [item['notation'] for item in columns] + ['value']

        # GET DATA AND ATTRIBUTES
        raw_data = []
        idx = 0
        for extra_filters in n_filters:
            query = sparql_env.get_template('data_and_attributes.sparql').render(**{
                'dataset': self.dataset,
                'columns': columns,
                'filters': filters + list(extra_filters),
                'group_dimensions': self.get_group_dimensions(),
                'notations': self.notations,
            })
            container = {}
            data = self._execute(query, as_dict=False)
            dict_data = []
            for item in data:
                dict_data.append(
                        dict(zip(columns_names, item)))
            raw_data.append(dict_data)

        # JOIN DATA
        def find_common(memo, item):
            join_set = [it[join_by] for it in item]
            temp_common = set(memo).intersection(set(join_set))
            return temp_common
        common = reduce(find_common, raw_data, [it[join_by] for it in raw_data[0]])

        # EXTRACT UNIQUE URIS FROM DATA
        by_category = defaultdict(list)
        uri_set = set()
        for obs_set in raw_data:
            for obs in obs_set:
                if obs[join_by] in common:
                    by_category[obs[join_by]].append(obs)
                    for key, value in obs.items():
                        if isinstance(value, basestring) and value.startswith('http://'):
                            uri_set.add(value)

        # GET LABELS FOR URIS
        labels = self.get_labels(uri_set)

        filtered_data = []
        # EXTRACT COMMON ROWS
        dimensions = ['x', 'y', 'z']
        single_keys = [f[0] for f in filters] + [join_by]
        for obs_list in by_category.values():
            idx = 0
            out = defaultdict(dict)
            for obs in obs_list:
                for key in columns_names:
                    if key not in single_keys:
                        out[key][dimensions[idx]] = obs[key]
                    else:
                        out[key] = obs[key]
                for k, v in out.items():
                    if k not in single_keys:
                        uri_labels = labels.get(v[dimensions[idx]], v[dimensions[idx]])
                        if uri_labels:
                            out[k][dimensions[idx]] = uri_labels
                    else:
                        uri_labels = labels.get(v, None)
                        if uri_labels:
                            out[k] = uri_labels
                idx+=1
            filtered_data.append(out)
        return filtered_data


    def get_revision(self):
        query = sparql_env.get_template('last_modified.sparql').render()
        timestamp = unicode(next(self._execute(query))['modified'])
        data_cache.ping(timestamp)
        return timestamp

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
