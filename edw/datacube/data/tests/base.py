import os
import pytest

SPARQL_ENDPOINT = os.environ.get('CUBE_SPARQL_ENDPOINT')
DATASET_URI = os.environ.get('CUBE_DATASET_URI')
pytest.config.SKIP_SPARQL_TESTS = not (SPARQL_ENDPOINT and DATASET_URI)


def sparql_test(func):
    return pytest.mark.skipif("config.SKIP_SPARQL_TESTS")(func)


_cube_notations_memo = {}


def create_cube():
    from edw.datacube.data.cube import Cube
    config = (SPARQL_ENDPOINT, DATASET_URI)
    cube = Cube(*config)
    if config not in _cube_notations_memo:
        _cube_notations_memo[config] = Cube(*config).notations
    cube.notations = _cube_notations_memo[config]
    return cube
