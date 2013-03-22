from .base import sparql_test, create_cube


@sparql_test
def test_dimensions_query():
    cube = create_cube()
    res = cube.get_dimensions()
    dimensions = {d['notation']: d for d in res}
    assert 'indicator' in dimensions
    assert 'ref-area' in dimensions
    assert dimensions['ref-area']['group_notation'] is None
    assert dimensions['indicator']['group_notation'] == 'indicator-group'


@sparql_test
def test_get_group_dimensions():
    cube = create_cube()
    res = cube.get_group_dimensions()
    assert res == ['breakdown-group', 'indicator-group']


@sparql_test
def test_unit_measure_labels_query():
    cube = create_cube()
    [res] = cube.get_dimension_labels(dimension='unit-measure', value='pc_ind')
    expected = {'short_label': '% ind', 'label': 'Percentage of individuals'}


@sparql_test
def test_indicator_labels_query():
    cube = create_cube()
    [res] = cube.get_dimension_labels(dimension='indicator', value='i_iusnet')
    expected = {
        'short_label': 'Participating in social networks',
        'label': 'participating in social networks'}
    assert expected['short_label'] == res['short_label']
    assert expected['label'] in res['label']


@sparql_test
def test_get_all_country_options():
    cube = create_cube()
    items = cube.get_dimension_options('ref-area')
    codes = [y['notation'] for y in items]
    assert len(codes) == 34
    assert 'DE' in codes
    assert 'ES' in codes
    assert 'IS' in codes
    assert 'EU27' in codes


@sparql_test
def test_get_available_country_options_for_year():
    cube = create_cube()
    items = cube.get_dimension_options('ref-area', [
        ('time-period', '2002'),
    ])
    codes = [y['notation'] for y in items]
    assert len(codes) == 17
    assert 'DE' in codes
    assert 'ES' in codes
    assert 'IS' not in codes
    assert 'EU27' not in codes


@sparql_test
def test_get_available_country_options_for_year_and_indicator():
    cube = create_cube()
    items = cube.get_dimension_options('ref-area', [
        ('time-period', '2002'),
        ('indicator', 'h_iacc'),
    ])
    codes = [y['notation'] for y in items]
    assert len(codes) == 15
    assert 'DE' in codes
    assert 'ES' not in codes
    assert 'IS' not in codes
    assert 'EU27' not in codes


@sparql_test
def test_get_available_indicator_group_options():
    cube = create_cube()
    items = cube.get_dimension_options('indicator-group')
    codes = [y['notation'] for y in items]
    assert len(codes) == 8
    assert 'internet-usage' in codes
    assert 'ebusiness' in codes


@sparql_test
def test_get_available_indicator_group_options_for_year_and_country():
    cube = create_cube()
    items = cube.get_dimension_options('indicator-group', [
        ('time-period', '2002'),
        ('ref-area', 'DK'),
    ])
    codes = [y['notation'] for y in items]
    assert len(codes) == 3
    assert 'internet-usage' in codes
    assert 'ebusiness' not in codes


@sparql_test
def test_get_available_year_options_for_indicator_group():
    cube = create_cube()
    items = cube.get_dimension_options('time-period', [
        ('indicator-group', 'mobile'),
    ])
    years = [y['notation'] for y in items]
    assert len(years) == 6
    assert '2010' in years
    assert '2002' not in years


@sparql_test
def test_get_indicators_in_group():
    cube = create_cube()
    items = cube.get_dimension_options('indicator', [
        ('indicator-group', 'ict-skills'),
    ])
    indicators = [i['notation'] for i in items]
    assert len(indicators) == 6
    assert 'i_skedu' in indicators
    assert 'e_broad' not in indicators


@sparql_test
def test_get_altlabel_for_group_dimension():
    cube = create_cube()
    items = cube.get_dimension_options('breakdown-group')
    label = [it['short_label'] for it in items
                if it['notation'] == 'byage'
            ][0]
    assert u'Age' == label


@sparql_test
def test_get_altlabel_for_not_group_dimension():
    cube = create_cube()
    items = cube.get_dimension_options('unit-measure')
    label = [it['short_label'] for it in items
                if it['notation'] == 'pc_ind'
            ][0]
    assert u'% ind' == label


@sparql_test
def test_get_years_for_xy_indicators():
    cube = create_cube()
    items = cube.get_dimension_options_xy('time-period',
        [('ref-area', 'ES')],
        [('indicator', 'i_iuse')],
        [('indicator', 'i_iu3g')],
    )
    years = [i['notation'] for i in items]
    assert len(years) == 5
    assert '2010' in years
    assert '2006' not in years
    assert '2004' not in years
