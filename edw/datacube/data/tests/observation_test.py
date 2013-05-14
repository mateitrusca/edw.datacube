from .base import sparql_test, create_cube


@sparql_test
def test_get_data_by_ref_area_with_dimension_filters():
    columns = ('ref-area', 'value')
    filters = [
        ('indicator', 'i_bfeu'),
        ('time-period', '2011'),
        ('breakdown', 'IND_TOTAL'),
        ('unit-measure', 'pc_ind'),
    ]
    cube = create_cube()
    points = list(cube.get_data(columns,  filters))
    assert len(points) == 31
    assert {'ref-area': 'IE',
            'ref-area-label': 'Ireland',
            'ref-area-short-label': None,
            'value': 0.2222} in points


@sparql_test
def test_get_data_by_time_period_with_dimension_filters():
    columns = ('time-period', 'value')
    filters = [
        ('indicator', 'i_bfeu'),
        ('breakdown', 'IND_TOTAL'),
        ('unit-measure', 'pc_ind'),
        ('ref-area', 'IE'),
    ]
    cube = create_cube()
    points = list(cube.get_data(columns, filters))
    assert {'time-period': '2011',
            'time-period-label': 'Year:2011',
            'time-period-short-label': '2011',
            'value': 0.2222} in points
    assert len(points) == 5


@sparql_test
def test_get_data_by_time_period_and_ref_area_with_dimension_filters():
    columns = ('time-period', 'ref-area', 'value')
    filters = [
        ('indicator', 'i_bfeu'),
        ('breakdown', 'IND_TOTAL'),
        ('unit-measure', 'pc_ind'),
    ]
    cube = create_cube()
    points = list(cube.get_data(columns, filters))
    assert {'time-period': '2011',
            'time-period-label': 'Year:2011',
            'time-period-short-label': '2011',
            'ref-area': 'IE',
            'ref-area-label': 'Ireland',
            'ref-area-short-label': None,
            'value': 0.2222} in points
    assert {'time-period': '2010',
            'time-period-label': 'Year:2010',
            'time-period-short-label': '2010',
            'ref-area': 'PT',
            'ref-area-label': 'Portugal',
            'ref-area-short-label': None,
            'value': 0.0609} in points
    assert len(points) == 161


@sparql_test
def test_get_data_by_time_period_and_ref_area_with_dimension_group_filters():
    columns = ('time-period', 'ref-area', 'value')
    filters = [
        ('indicator-group', 'ecommerce'),
        ('indicator', 'i_bfeu'),
        ('breakdown-group', 'total'),
        ('breakdown', 'IND_TOTAL'),
        ('unit-measure', 'pc_ind'),
    ]
    cube = create_cube()
    points = list(cube.get_data(columns, filters))
    assert {'time-period': '2011',
            'time-period-label': 'Year:2011',
            'time-period-short-label': '2011',
            'ref-area': 'IE',
            'ref-area-label': 'Ireland',
            'ref-area-short-label': None,
            'value': 0.2222} in points
    assert {'time-period': '2010',
            'time-period-label': 'Year:2010',
            'time-period-short-label': '2010',
            'ref-area': 'PT',
            'ref-area-label': 'Portugal',
            'ref-area-short-label': None,
            'value': 0.0609} in points
    assert len(points) == 161


@sparql_test
def test_get_same_observation_in_two_dimensions():
    filters = [
        ('time-period', '2011'),
        ('indicator', 'i_bfeu'),
        ('breakdown', 'IND_TOTAL'),
        ('unit-measure', 'pc_ind'),
        ('ref-area', 'IE'),
    ]
    cube = create_cube()
    points = list(cube.get_data_xy('ref-area', filters, [], []))
    assert len(points) == 1
    assert points[0]['value'] == {'x': 0.2222, 'y': 0.2222}

@sparql_test
def test_get_observations_with_labels_xy():
    filters = [
        ('time-period', '2011'),
        ('indicator', 'i_bfeu'),
        ('breakdown', 'IND_TOTAL'),
        ('unit-measure', 'pc_ind'),
    ]
    cube = create_cube()
    points = list(cube.get_data_xy('ref-area', filters, [], []))
    assert points[0]['indicator']['label'].startswith(
        'Individuals ordering goods')


@sparql_test
def test_get_xy_observations_with_all_breakpoints():
    filters = [
        ('time-period', '2011'),
        ('indicator', 'i_bfeu'),
        ('breakdown', 'IND_TOTAL'),
        ('unit-measure', 'pc_ind'),
    ]
    cube = create_cube()
    points = list(cube.get_data_xy('ref-area', filters, [], []))
    assert points[0]['indicator_x']['label'].startswith(
        'Individuals ordering goods')


@sparql_test
def test_get_same_observation_in_xyz_dimensions():
    filters = [
        ('time-period', '2011'),
        ('indicator', 'i_bfeu'),
        ('breakdown', 'IND_TOTAL'),
        ('unit-measure', 'pc_ind'),
        ('ref-area', 'IE'),
    ]
    cube = create_cube()
    points = list(cube.get_data_xyz('ref-area', filters, [], [], []))
    assert len(points) == 1
    assert points[0]['value'] == {'x': 0.2222, 'y': 0.2222, 'z': 0.2222}


@sparql_test
def test_get_xy_observations_for_2_countries_all_years():
    filters = [
        ('indicator', 'i_bfeu'),
        ('breakdown', 'IND_TOTAL'),
        ('unit-measure', 'pc_ind'),
    ]
    x_filters = [('ref-area', 'IE')]
    y_filters = [('ref-area', 'DK')]
    cube = create_cube()
    pts = list(cube.get_data_xy('time-period', filters, x_filters, y_filters))
    assert len(pts) == 5
    assert filter(
               lambda item: item['time-period']['notation'] == '2011',
               pts)[0]['value'] == {'x': 0.2222, 'y': 0.2795}
    assert filter(
               lambda item: item['time-period']['notation'] == '2012',
               pts)[0]['value'] == {'x': 0.2811, 'y': 0.2892}


@sparql_test
def test_get_xyz_observations_for_3_countries_all_years():
    filters = [
        ('indicator', 'i_bfeu'),
        ('breakdown', 'IND_TOTAL'),
        ('unit-measure', 'pc_ind'),
    ]
    x_filters = [('ref-area', 'IE')]
    y_filters = [('ref-area', 'DK')]
    z_filters = [('ref-area', 'AT')]
    cube = create_cube()
    pts = list(cube.get_data_xyz('time-period', filters, x_filters, y_filters, z_filters))
    assert len(pts) == 5
    assert filter(
               lambda item: item['time-period']['notation'] == '2008',
               pts)[0]['value'] == {'x': 0.1707, 'y': 0.1976, 'z': 0.2447}


@sparql_test
def test_get_observations_with_all_attributes():
    cube = create_cube()
    filters = [ ('breakdown', 'TOTAL'),
                ('indicator', 'bb_dsl'),
                ('indicator-group', 'broadband'),
                ('ref-area', 'EU27'),
                ('unit-measure', 'pc_lines')]
    result = list(cube.get_observations(filters))
    assert len(result) == 8
    assert result[0]['value'] == 0.7706
    assert result[0]['indicator']['label'].startswith('Broadband take-up')
    assert result[0]['indicator']['short-label'].startswith('DSL lines')
