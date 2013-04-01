from Products.Five.browser import BrowserView
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
                'image': '%s/thumbnail/image_preview' % url,
                'title': obj.title_or_id(),
                'description': obj.Description(),
            })
        return jsonify(self.request, data)
