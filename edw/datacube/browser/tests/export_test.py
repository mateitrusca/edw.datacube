from mock import Mock, MagicMock, call
import csv
import simplejson as json
import pytest
from StringIO import StringIO
from edw.datacube.browser.export import ExportCSV


def test_columns_csv_export():
    exporter = ExportCSV(MagicMock(), MagicMock())
    out = StringIO()
    series = [{
        'data': [
            {
                'code': 'SK',
                'name': 'Slovakia',
                'y': 1

            }
        ],
        'name': 'series1',
        'notation': None
    }]
    exporter.datapoints(out, series)
    out.seek(0)
    csv_output = out.read().split('\r\n')
    assert csv_output[0].split(',') == ['series', 'code', 'y'];
    assert csv_output[1].split(',') == ['series1', 'SK', '1']


def test_columns_csv_export_multiseries():
    exporter = ExportCSV(MagicMock(), MagicMock())
    headers = ['series', 'code', 'y'];
    out = StringIO()
    series = [
        {
            'data': [
                {
                    'code': 'SK',
                    'name': 'Slovakia',
                    'y': 1

                }
            ],
            'name': 'series1',
            'notation': None
        },
        {
            'data': [
                {
                    'code': 'AB',
                    'name': 'ABCD',
                    'y': 2

                }
            ],
            'name': 'series2',
            'notation': None
        }
    ]
    exporter.datapoints(out, series)
    out.seek(0)
    csv_output = out.read().split('\r\n')
    assert csv_output[1].split(',') == ['series1', 'SK', '1']
    assert csv_output[2].split(',') == ['series2', 'AB', '2']


def test_lines_csv_export():
    exporter = ExportCSV(MagicMock(), MagicMock())
    out = StringIO()
    series = [
        {
            'data': [
                {
                    'code': '2000',
                    'name': 'Year:2000',
                    'y': 1

                }
            ],
            'name': 'series1',
            'notation': None
        },
    ]
    exporter.datapoints(out, series)
    out.seek(0)
    csv_output = out.read().split('\r\n')
    assert csv_output[1].split(',') == ['series1', '2000', '1']


def test_scatter_csv_export():
    exporter = ExportCSV(MagicMock(), MagicMock())
    out = StringIO()
    series = [
        [
            {
                'data': [
                    {
                        'name': 'AT',
                        'x': 1,
                        'y': 1

                    }
                ],
                'name': 'Austria'
            },
        ]
    ]
    exporter.datapoints_n(out, series)
    out.seek(0)
    csv_output = out.read().split('\r\n')
    assert csv_output[0].split(',') == ['series', 'name', 'x', 'y'];
    assert csv_output[1].split(',') == ['Austria', 'AT', '1', '1']


def test_bubbles_csv_export():
    exporter = ExportCSV(MagicMock(), MagicMock())
    out = StringIO()
    series = [
        [
            {
                'data': [
                    {
                        'name': 'AT',
                        'x': 1,
                        'y': 1,
                        'z': 1

                    }
                ],
                'name': 'Austria'
            },
        ]
    ]
    exporter.datapoints_n(out, series)
    out.seek(0)
    csv_output = out.read().split('\r\n')
    assert csv_output[0].split(',') == ['series', 'name', 'x', 'y', 'z'];
    assert csv_output[1].split(',') == ['Austria', 'AT', '1', '1', '1']


def test_bar_profile_csv_export():
    exporter = ExportCSV(MagicMock(), MagicMock())
    out = StringIO()
    series = [
        {
            'data': [
                {
                    'attributes': {
                        'time-period': {
                            'notation': '2000'
                        }
                    },
                    'code': 'notation',
                    'name': 'long_label',
                    'eu': 0.5,
                    'original': 0.9,
                    'y': 2,

                }
            ],
            'name': 'Austria'
        },
    ]
    exporter.datapoints_profile(out, series)
    out.seek(0)
    csv_output = out.read().split('\r\n')
    assert csv_output[0].split(',') == [
            'period', 'name', 'eu', 'original']
    assert csv_output[1].split(',') == [
            '2000', 'long_label', '0.5', '0.9']


def test_table_profile_csv_export():
    exporter = ExportCSV(MagicMock(), MagicMock())
    out = StringIO()
    series = [
        {
            'data': {
                'latest': 2010,
                'ref-area': {
                    'label': 'Austria'
                },
                'table':{
                    'some-key': {
                        '2009': 0.8,
                        '2010': 0.9,
                        'eu': 52,
                        'name': 'long-label',
                        'rank': 15
                    },
                    'some-other-key': {
                        '2009': 0.8,
                        'eu': 52,
                        'name': 'other-long-label',
                        'rank': 15
                    }
                }
            }
        }
    ]
    exporter.datapoints_profile_table(out, series)
    out.seek(0)
    csv_output = out.read().split('\r\n')
    assert csv_output[0].split(',') == [
            'country', 'indicator', '2009', '2010', 'EU27 value 2010', 'rank']
    assert csv_output[1].split(',') == [
            'Austria', 'long-label', '0.8', '0.9', '52', '15']
    assert csv_output[2].split(',') == [
            'Austria', 'other-long-label', '0.8', '-', '52', '15']


def test_formatter_decision():
    exporter = ExportCSV(MagicMock(), MagicMock())
    series = [
        {
            'data': [
                {
                    'code': '2000',
                    'name': 'year:2000',
                    'y': 1

                }
            ],
            'name': 'series1',
            'notation': None
        },
    ]
    exporter.datapoints = Mock()
    exporter.datapoints_n = Mock()

    exporter.request.form = {
        'chart_data': json.dumps(series),
        'chart_type': 'columns'
    }
    exporter.export()
    assert(exporter.datapoints.call_count == 1)

    exporter.request.form = {
        'chart_data': json.dumps(series),
        'chart_type': 'bubbles'
    }
    exporter.export()
    assert(exporter.datapoints_n.call_count == 1)

    exporter.request.form = {
        'chart_data': json.dumps(series),
        'chart_type': 'scatter'
    }
    exporter.export()
    assert(exporter.datapoints_n.call_count == 2)
