from django.conf import settings

class BaseEngine(object):
    """
    Abstract storage engine base class.
    """
    def __init__(self, using=None):
    	self.using = using
    	self.options = settings.SUPERASSETS_STORAGES.get(self.using, {})
    def put(self, filename, contents):
        raise NotImplementedError
    def url(self, filename):
        raise NotImplementedError