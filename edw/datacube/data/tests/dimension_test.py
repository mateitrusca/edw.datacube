from .base import sparql_test, create_cube


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
        'short_label': "Participating in social networks",
        'label': "participating in social networks, over the internet"}
    assert res['short_label'] == expected['short_label']
    assert res['label'].startswith(expected['label'])


@sparql_test
def test_period_labels_query():
    cube = create_cube()
    [res] = cube.get_dimension_labels(dimension='time-period', value='2006')
    expected = {
        'short_label': '2006',
        'label': 'Year:2006'}
    assert expected['short_label'] == res['short_label']
    assert expected['label'] == res['label']


@sparql_test
def test_get_all_country_options():
    cube = create_cube()
    items = cube.get_dimension_options('ref-area')
    codes = [y['notation'] for y in items]
    assert len(codes) == 47
    assert 'DE' in codes
    assert 'ES' in codes
    assert 'BG' in codes
    assert 'EU27' in codes


@sparql_test
def test_get_available_country_options_for_year():
    cube = create_cube()
    items = cube.get_dimension_options('ref-area', [
        ('time-period', '2006'),
        ('indicator', 'e_igovrt'),
    ])
    codes = [y['notation'] for y in items]
    print codes
    assert len(codes) == 30
    assert 'EL' in codes
    assert 'EU27' in codes
    assert 'HR' not in codes


@sparql_test
def test_group_notations(monkeypatch):
    cube = create_cube()
    items = cube.get_dimension_options('indicator', [
        ('indicator-group', 'ict-skills'),
    ])
    assert items[0]['group_notation'] == 'ict-skills'


@sparql_test
def test_get_available_country_options_for_year_and_indicator():
    cube = create_cube()
    items = cube.get_dimension_options('ref-area', [
        ('time-period', '2002'),
        ('indicator', 'h_iacc'),
    ])
    codes = [y['notation'] for y in items]
    assert len(codes) == 19
    assert 'DE' in codes
    assert 'ES' not in codes
    assert 'BG' not in codes
    assert 'EU27' not in codes


@sparql_test
def test_get_available_indicator_group_options():
    cube = create_cube()
    items = cube.get_dimension_options('indicator-group')
    codes = [y['notation'] for y in items]
    assert len(codes) == 14
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
    assert len(codes) == 6
    assert 'internet-usage' in codes
    assert 'ebusiness' not in codes


@sparql_test
def test_get_available_year_options_for_indicator_group():
    cube = create_cube()
    items = cube.get_dimension_options('time-period', [
        ('indicator-group', 'mobile'),
    ])
    years = [y['notation'] for y in items]
    assert len(years) == 7
    assert '2012' in years
    assert '2002' not in years


@sparql_test
def test_get_indicators_in_group():
    cube = create_cube()
    items = cube.get_dimension_options('indicator', [
        ('indicator-group', 'ict-skills'),
    ])
    indicators = [i['notation'] for i in items]
    assert len(indicators) == 11
    assert 'i_skedu' in indicators
    assert 'P_IUSE' in indicators
    assert 'e_broad' not in indicators


@sparql_test
def test_get_altlabel_for_group_dimension():
    cube = create_cube()
    items = cube.get_dimension_options('breakdown-group')
    label = [it['short_label'] for it in items
                if it['notation'] == 'byage3classes'
            ][0]
    assert u'Age (3 classes)' == label


@sparql_test
def test_get_altlabel_for_not_group_dimension():
    cube = create_cube()
    items = cube.get_dimension_options('unit-measure')
    label = [it['short_label'] for it in items
                if it['notation'] == 'pc_ind'
            ][0]
    assert u'% of individuals' == label


@sparql_test
def test_get_years_for_xy_indicators():
    cube = create_cube()
    items = cube.get_dimension_options_xy('time-period',
        [('ref-area', 'ES')],
        [('indicator', 'i_iuse')],
        [('indicator', 'i_iu3g')],
    )
    years = [i['notation'] for i in items]
    assert len(years) == 6
    assert '2010' in years
    assert '2012' in years
    assert '2006' not in years
    assert '2004' not in years


@sparql_test
def test_get_years_for_xyz_indicators():
    cube = create_cube()
    items = cube.get_dimension_options_xyz('time-period',
        [('ref-area', 'ES')],
        [('indicator', 'bb_dsl')],
        [('indicator', 'bb_penet')],
        [('indicator', 'bb_ne')]
    )
    years = [i['notation'] for i in items]
    assert len(years) == 17
    assert '2007-12' in years
    assert '2012-06' in years
    assert '2012' not in years


@sparql_test
def test_get_indicator_metadata():
    cube = create_cube()
    res = cube.get_dimension_option_metadata('indicator', 'i_iuse')
    assert res['label'].startswith("Individuals who are regular")
    assert res['short_label'] == "Regular internet users"
    assert res['definition'] == ("Individuals using the internet at least "
                                 "once a week in the last 3 months.")


@sparql_test
def test_get_breakdown_metadata():
    cube = create_cube()
    res = cube.get_dimension_option_metadata('breakdown', 'IND_TOTAL')
    assert res['label'] == "All Individuals (aged 16-74)"
    assert res['short_label'] == "All individuals"
    assert 'definition' not in res
    assert 'note' not in res
    assert 'source_label' not in res


@sparql_test
def test_get_indicator_source_metadata():
    cube = create_cube()
    res = cube.get_dimension_option_metadata('indicator', 'i_iuse')
    assert res['label'].startswith("Individuals who are regular ")
    assert res['source_label'] == "Eurostat - ICT Households survey"
    assert res['source_definition'] == (
        "Eurostat - Community survey on ICT "
        "usage in Households and by Individuals")
    assert res['source_notes'] == (
        u"Extraction from HH/Indiv comprehensive database "
        u"(ACCESS) version\xa029 April 2013")
    assert res['source_url'] == (
        "http://epp.eurostat.ec.europa.eu/portal/page/"
        "portal/information_society/introduction")

@sparql_test
def test_dump_has_output():
    cube = create_cube()
    res = cube.dump()
    assert(res.next())

@sparql_test
def test_dump_row_fields():
    cube = create_cube()
    res = cube.dump()
    expected = set([
        'unit_measure',
        'indicator',
        'time_period',
        'value',
        'ref_area',
        'breakdown'])
    assert expected.difference(set(res.next().keys())) == set([])


@sparql_test
def test_get_labels():
    import sparql
    cube = create_cube()
    uri_list = ['http://reference.data.gov.uk/id/gregorian-year/2007',
                'http://reference.data.gov.uk/id/gregorian-year/2009']
    res = cube.get_labels(uri_list)
    assert sorted(res.keys()) == uri_list
    assert res[uri_list[1]]['notation'] == '2009'
    assert res[uri_list[1]]['short_label'] == '2009'


@sparql_test
def test_indicator_groups_are_sorted():
    cube = create_cube()
    res = cube.get_dimension_options(dimension='indicator-group')
    codes = [y['notation'] for y in res]
    assert codes == ['broadband', 'mobile', 'bbquality', 'internet-usage',
                     'internet-services', 'egovernment', 'ecommerce',
                     'ebusiness', 'ict-skills', 'ict-edu', 'eHealth', 'research-and-development', 'ict-sector', 'back']
