from mock import Mock, MagicMock, call
import csv
import simplejson as json
import pytest
from StringIO import StringIO
from edw.datacube.browser.export import ExportCSV


def test_columns_csv_export():
    exporter = ExportCSV(MagicMock(), MagicMock())
    headers = ['series', 'code', 'y'];
    out = StringIO()
    writer = csv.DictWriter(out, headers, restval='')
    writer.writeheader()
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
    exporter.datapoints(writer, series)
    out.seek(0)
    csv_output = out.read().split('\r\n')
    assert csv_output[0].split(',') == headers
    assert csv_output[1].split(',') == ['series1', 'SK', '1']


def test_columns_csv_export_multiseries():
    exporter = ExportCSV(MagicMock(), MagicMock())
    headers = ['series', 'code', 'y'];
    out = StringIO()
    writer = csv.DictWriter(out, headers, restval='')
    writer.writeheader()
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
    exporter.datapoints(writer, series)
    out.seek(0)
    csv_output = out.read().split('\r\n')
    assert csv_output[1].split(',') == ['series1', 'SK', '1']
    assert csv_output[2].split(',') == ['series2', 'AB', '2']


def test_lines_csv_export():
    exporter = ExportCSV(MagicMock(), MagicMock())
    headers = ['series', 'code', 'y'];
    out = StringIO()
    writer = csv.DictWriter(out, headers, restval='')
    writer.writeheader()
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
    exporter.datapoints(writer, series)
    out.seek(0)
    csv_output = out.read().split('\r\n')
    assert csv_output[1].split(',') == ['series1', '2000', '1']

