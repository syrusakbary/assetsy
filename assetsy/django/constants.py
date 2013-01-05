from django.conf import settings

IF_DEBUG = getattr(settings,'DEBUG',False)
IF_NOT_DEBUG = not IF_DEBUG