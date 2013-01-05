from django.conf.urls.defaults import *
local_media_url = 'statica'

urlpatterns = patterns('assetsy.django.views',
    url(r'^%s/(?P<path>.*)$' % local_media_url, 'static_serve'),
)