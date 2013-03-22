import time
import urllib2
import os
import logging
import jinja2
import sparql

SPARQL_DEBUG = bool(os.environ.get('SPARQL_DEBUG') == 'on')

logger = logging.getLogger(__name__)

sparql_env = jinja2.Environment(loader=jinja2.PackageLoader(__name__))

# DATA_REVISION should be the time of last database modification
DATA_REVISION = str(int(time.time()))


class QueryError(Exception):
    pass


def literal_pairs(pairs):
    return [(sparql.Literal(a), sparql.Literal(b)) for a, b in pairs]


class Cube(object):

    def __init__(self, endpoint, dataset):
        self.endpoint = endpoint
        self.dataset = sparql.IRI(dataset)

    def _execute(self, query, as_dict=True):
        if SPARQL_DEBUG:
            logger.info('Running query: \n%s', query)
        try:
            res = sparql.query(self.endpoint, query)
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

    def get_dimension_labels(self, dimension, value):
        query = sparql_env.get_template('dimension_label.sparql').render(**{
            'dataset': self.dataset,
            'dimension': dimension,
            'value': value
        })
        return list(self._execute(query))

    def get_dimensions(self):
        query = sparql_env.get_template('dimensions.sparql').render(**{
            'dataset': self.dataset,
        })
        return list(self._execute(query))

    def get_group_dimensions(self):
        query = sparql_env.get_template('group_dimensions.sparql').render(**{
            'dataset': self.dataset,
        })
        return sorted([r['group_notation'] for r in self._execute(query)])

    def get_dimension_options(self, dimension, filters=[]):
        query = sparql_env.get_template('dimension_options.sparql').render(**{
            'dataset': self.dataset,
            'dimension_code': sparql.Literal(dimension),
            'filters': literal_pairs(filters),
            'group_dimensions': self.get_group_dimensions(),
        })
        return list(self._execute(query))

    def get_dimension_options_xy(self, dimension,
                                 filters, x_filters, y_filters):
        tmpl = sparql_env.get_template('dimension_options_xy.sparql')
        query = tmpl.render(**{
            'dataset': self.dataset,
            'dimension_code': sparql.Literal(dimension),
            'filters': literal_pairs(filters),
            'x_filters': literal_pairs(x_filters),
            'y_filters': literal_pairs(y_filters),
            'group_dimensions': self.get_group_dimensions(),
        })
        return list(self._execute(query))

    def get_data(self, fields, filters):
        assert fields[-1] == 'value', "Last column must be 'value'"
        query = sparql_env.get_template('data.sparql').render(**{
            'dataset': self.dataset,
            'columns': [sparql.Literal(c) for c in fields[:-1]],
            'filters': literal_pairs(filters),
            'group_dimensions': self.get_group_dimensions(),
        })

        columns = []
        for f in fields:
            columns.append(f);
            columns.append('%s-label' %f)

        for row in self._execute(query, as_dict=False):
            yield dict(zip(columns, row))

    def get_data_xy(self, columns, xy_columns, filters, x_filters, y_filters):
        assert xy_columns == ['value']
        query = sparql_env.get_template('data_xy.sparql').render(**{
            'dataset': self.dataset,
            'filters': literal_pairs(filters),
            'x_filters': literal_pairs(x_filters),
            'y_filters': literal_pairs(y_filters),
            'columns': [sparql.Literal(c) for c in columns],
            'group_dimensions': self.get_group_dimensions(),
        })
        for row in self._execute(query, as_dict=False):
            out = dict(zip(columns, row))
            out['value'] = {'x': row[-2], 'y': row[-1]}
            yield out

    def get_revision(self):
        return DATA_REVISION
