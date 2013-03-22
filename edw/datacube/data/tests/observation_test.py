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
            'time-period-label': 'British Year:2011',
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
            'time-period-label': 'British Year:2011',
            'ref-area': 'IE',
            'ref-area-label': 'Ireland',
            'value': 0.2222} in points
    assert {'time-period': '2010',
            'time-period-label': 'British Year:2010',
            'ref-area': 'PT',
            'ref-area-label': 'Portugal',
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
            'time-period-label': 'British Year:2011',
            'ref-area': 'IE',
            'ref-area-label': 'Ireland',
            'value': 0.2222} in points
    assert {'time-period': '2010',
            'time-period-label': 'British Year:2010',
            'ref-area': 'PT',
            'ref-area-label': 'Portugal',
            'value': 0.0609} in points
    assert len(points) == 161


@sparql_test
def test_get_same_observation_in_two_dimensions():
    xy_columns = ['value']
    filters = [
        ('time-period', '2011'),
        ('indicator', 'i_bfeu'),
        ('breakdown', 'IND_TOTAL'),
        ('unit-measure', 'pc_ind'),
        ('ref-area', 'IE'),
    ]
    cube = create_cube()
    points = list(cube.get_data_xy((), xy_columns, filters, (), ()))
    assert len(points) == 1
    assert points[0] == {'value': {'x': 0.2222, 'y': 0.2222}}


@sparql_test
def test_get_xy_observations_for_2_countries_all_years():
    columns = ['time-period']
    xy_columns = ['value']
    filters = [
        ('indicator', 'i_bfeu'),
        ('breakdown', 'IND_TOTAL'),
        ('unit-measure', 'pc_ind'),
    ]
    x_filters = [('ref-area', 'IE')]
    y_filters = [('ref-area', 'DK')]
    cube = create_cube()
    pts = list(cube.get_data_xy(columns, xy_columns,
                                filters, x_filters, y_filters))
    assert len(pts) == 5
    assert {'time-period': '2011', 'value': {'x': 0.2222, 'y': 0.2795}} in pts
    assert {'time-period': '2012', 'value': {'x': 0.2811, 'y': 0.2892}} in pts
