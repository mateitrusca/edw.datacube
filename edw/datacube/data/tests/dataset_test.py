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
    assert res['license'] == 'http://joinup.ec.europa.eu/software/page/eupl'
