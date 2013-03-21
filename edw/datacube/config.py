"""Common configuration constants
"""
PROJECTNAME = 'edw.datacube'

ADD_PERMISSIONS = {
    'DataCube':
        'edw.datacube: Add DataCube',
}

from zope.i18nmessageid.message import MessageFactory
_ = MessageFactory('edw')
