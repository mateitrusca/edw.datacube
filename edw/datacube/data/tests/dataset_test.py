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
