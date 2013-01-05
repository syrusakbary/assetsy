from django.http import HttpResponse, HttpResponseNotModified
from django.views.static import was_modified_since
from django.utils.http import http_date
# from django.views.static import serve
# from django.conf import settings
import mimetypes


from assetsy.django.env import get_env
env = get_env()

def static_serve(request, path):
    """
    Given a request for a media asset, this view does the necessary wrangling
    to get the correct thing delivered to the user. This can also emulate the
    combo behavior seen when SERVE_REMOTE == False and EMULATE_COMBO == True.
    """
    # Django static serve view.
    #dr = os.path.join(settings.ROOT_PATH, '../static/')
    mimetype, encoding = mimetypes.guess_type(path)
    mimetype = mimetype or 'application/octet-stream'
    env.process()

    outputs = env.outputs()
    resource = outputs[path]
    last_modified = resource.last_modified
    size = len(resource.content)
    if not was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'),
                              last_modified, size):
        return HttpResponseNotModified(mimetype=mimetype)

    response = HttpResponse(resource.content, mimetype=mimetype)
    response["Last-Modified"] = http_date(last_modified)
    response["Content-Length"] = size

    #resp = serve(request, path, document_root=dr, show_indexes=True)
    #resp.content = client.process(resp.content, resp['Content-Type'], path)
    return response
