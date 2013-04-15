from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName
from zope.component import queryUtility
from plone.registry.interfaces import IRegistry
from edw.datacube.interfaces import IDataCubeSettings

from .query import jsonify


class DataCubeView(BrowserView):
    _settings = None

    @property
    def settings(self):
        """ Settings
        """
        if self._settings is None:
            self._settings = queryUtility(
                IRegistry).forInterface(IDataCubeSettings, False)
        return self._settings

    def relations(self):
        data = []
        for obj in self.context.getBRefs():
            url = obj.absolute_url()
            thumbnail_field = obj.getField('thumbnail')
            thumbnail = thumbnail_field.getAccessor(obj)()
            if thumbnail:
                image_url = '%s/thumbnail' % url
            else:
                image_url = self.settings.visualization_thumbnail
            data.append({
                'id': obj.getId(),
                'portal_type': obj.portal_type,
                'url': url,
                'image': image_url,
                'title': obj.title_or_id(),
                'description': obj.Description(),
            })
        return jsonify(self.request, data)

    def getItemState(self, obj):
        """ Item state
        """
        wft = getToolByName(self.context, 'portal_workflow')
        return wft.getInfoFor(obj, 'review_state', '')
