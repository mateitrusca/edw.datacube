from .base import sparql_test, create_cube


@sparql_test
def test_notations_lookup_finds_values():
    cube = create_cube()
    ns_and_notation = ('indicator', 'bb_lines')
    bb_lines_uri = ('http://semantic.digital-agenda-data.eu/'
                    'codelist/indicator/bb_lines')
    assert (cube.notations.lookup_notation('indicator', 'bb_lines')['uri']
            == bb_lines_uri)
    assert cube.notations.lookup_uri(bb_lines_uri)['notation'] == 'bb_lines'
