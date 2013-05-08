import os
import time
from contextlib import contextmanager


def create_cube():
    from edw.datacube.data.cube import Cube
    SPARQL_ENDPOINT = os.environ.get('CUBE_SPARQL_ENDPOINT')
    DATASET_URI = os.environ.get('CUBE_DATASET_URI')
    return Cube(SPARQL_ENDPOINT, DATASET_URI)


@contextmanager
def measure(name):
    t0 = time.time()
    try:
        yield
    finally:
        print u"{duration:6.3f} {name}".format(**{
            'name': name,
            'duration': time.time() - t0,
        })


def run_benchmarks():
    cube = create_cube()

    with measure('load notations mapping'):
        cube.notations._update()

    with measure('dimension values (all indicators)'):
        list(cube.get_dimension_options('indicator'))

    with measure('dimension values (breakdowns for indicator)'):
        list(cube.get_dimension_options('breakdown', [
            ('indicator', 'e_adesucu'),
        ]))

    with measure('datapoints'):
        list(cube.get_data(['ref-area', 'value'], [
            ('indicator', 'AAAA_cov'),
            ('time-period', '2012'),
            ('breakdown-group', 'total'),
            ('breakdown', 'TOTAL'),
            ('unit-measure', 'pc_websites'),
        ]))

    with measure('dimension_values_xy (years)'):
        list(cube.get_dimension_options_xy('time-period', [
        ], [
            ('indicator', 'bb_dsl'),
            ('breakdown', 'TOTAL'),
            ('unit-measure', 'pc_lines'),
        ], [
            ('indicator', 'e_adesucu'),
            ('breakdown', 'ent_all_xfin'),
            ('unit-measure', 'pc_ent'),
        ]))

    with measure('dimension_values_xy (countries)'):
        list(cube.get_dimension_options_xy('ref-area', [
            ('time-period', '2004'),
        ], [
            ('indicator', 'bb_dsl'),
            ('breakdown', 'TOTAL'),
            ('unit-measure', 'pc_lines'),
        ], [
            ('indicator', 'e_adesucu'),
            ('breakdown', 'ent_all_xfin'),
            ('unit-measure', 'pc_ent'),
        ]))

    with measure('dimension_values_xyz (countries)'):
        list(cube.get_dimension_options_xyz('ref-area', [
            ('time-period', '2009'),
        ], [
            ('breakdown', 'ent_all_xfin'),
            ('indicator', 'e_adesucu'),
            ('unit-measure', 'pc_ent'),
        ], [
            ('breakdown', 'TOTAL'),
            ('indicator', 'FOA_cit'),
            ('unit-measure', 'pc_pub_serv_for_citizen'),
        ], [
            ('breakdown', 'IND_TOTAL'),
            ('indicator', 'i_iu3g'),
            ('unit-measure', 'pc_ind'),
        ]))


if __name__ == '__main__':
    import logging
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.getLogger().setLevel(logging.INFO)
    run_benchmarks()
