from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName
from .query import jsonify


class DataCubeView(BrowserView):

    def relations(self):
        data = []
        for obj in self.context.getBRefs():
            url = obj.absolute_url()
            data.append({
                'id': obj.getId(),
                'portal_type': obj.portal_type,
                'url': url,
                'image': '%s/thumbnail' % url,
                'title': obj.title_or_id(),
                'description': obj.Description(),
            })
        return jsonify(self.request, data)

    def getItemState(self, obj):
        """ Item state
        """
        wft = getToolByName(self.context, 'portal_workflow')
        return wft.getInfoFor(obj, 'review_state', '')
