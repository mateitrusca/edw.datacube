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
