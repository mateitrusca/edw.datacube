from mock import ANY
from .base import sparql_test, create_cube


@sparql_test
def test_all_datasets_query_returns_the_dataset():
    cube = create_cube()
    res = cube.get_datasets()
    dataset = {
        'uri': 'http://semantic.digital-agenda-data.eu/dataset/scoreboard',
        'title': 'Digital Agenda Scoreboard Dataset',
    }
    assert dataset in res


@sparql_test
def test_dataset_metadata():
    cube = create_cube()
    dataset = 'http://semantic.digital-agenda-data.eu/dataset/scoreboard'
    res = cube.get_dataset_metadata(dataset)
    assert res['title'] == "Digital Agenda Scoreboard Dataset"
    assert "You can also browse the data" in res['description']
    assert res['license'] == 'http://creativecommons.org/publicdomain/zero/1.0/'

@sparql_test
def test_dataset_dimensions_metadata():
    cube = create_cube()
    res = cube.get_dimensions()
    assert {'notation': 'ref-area',
            'label': "Country",
            'comment': ANY} in res['dimension']
    notations = lambda type_label: [d['notation'] for d in res[type_label]]
    assert sorted(res) == ['attribute', 'dimension',
                           'group dimension', 'measure']
    assert notations('dimension') == ['indicator', 'breakdown', 'unit-measure',
                                      'ref-area', 'time-period']
    assert notations('group dimension') == ['indicator-group',
                                            'breakdown-group']
    assert notations('attribute') == ['unit-measure', 'flag', 'note']
    assert [d['label'] for d in res['measure']] == ['Observation']

@sparql_test
def test_dataset_dimensions_flat_list():
    cube = create_cube()
    res = cube.get_dimensions(flat=True)
    assert [d['notation'] for d in res] == [
        None,
        'unit-measure',
        'flag',
        'note',
        'indicator-group',
        'indicator',
        'breakdown-group',
        'breakdown',
        'unit-measure',
        'ref-area',
        'time-period',
    ]
