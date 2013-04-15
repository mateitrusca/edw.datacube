""" Interfaces
"""
from zope.interface import Interface
from zope import schema
from zope.i18nmessageid import MessageFactory
_ = MessageFactory("edw")


class IDataCube(Interface):
    """Description of the Example Type"""

    # -*- schema definition goes here -*-


class IDataCubeSettings(Interface):
    """ Settings for datacube
    """
    datacube_thumbnail = schema.TextLine(
            title=_(u"DataCube thumbnail"),
            description=_(u"Default picture URL when no thumbnail is available"),
            required=True,
            default=u"++resource++scoreboard.theme.images/connect_thumbnail.png"
    )

    visualization_thumbnail = schema.TextLine(
            title=_(u"Visualization thumbnail"),
            description=_(u"Default picture URL when no thumbnail is available"),
            required=True,
            default=u"++resource++scoreboard.theme.images/map_thumbnail.png"
    )
